#!/usr/bin/python3 -u

from py_console import console
import hcl
import json
import os
import requests
import sys

class Workspace(object):
    def __init__(self, tf_workspace_name, platform, tf_version, org):
        self.platform = platform
        self.base_url = 'https://app.terraform.io'
        self.org = org
        self.get_org()
        self.get_terraformrc_path()
        self.org_url = self.base_url + '/api/v2/organizations/' + self.org
        self.workspaces_url = self.org_url + '/workspaces'
        self.token_environment_variable_name = "TF_TOKEN"
        self.tfc_config_template = {
            "credentials": {
                "app.terraform.io": {
                    "token": "temp_value"
                }
            },
            "disable_checkpoint": "true",
            "plugin_cache_dir": self.cache_dir
        }
        self.tf_headers = {
            "Content-Type": "application/vnd.api+json",
            "Authorization": "Bearer {}".format(self.get_token()),
        }
        self.create_workspace(tf_workspace_name, tf_version)

    def get_org(self):
        if not self.org:
            console.error("  Please add 'tf_cloud_org' to the local config file !\n", showTime=False)
            sys.exit(2)

    def get_terraformrc_path(self):
        if self.platform == 'windows':
            self.config_file = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "terraform.rc")
            self.cache_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "terraform.d", "plugin-cache")
        else:
            self.config_file = os.path.join(os.path.expanduser("~"), ".terraformrc")
            self.cache_dir = os.path.join(os.path.expanduser("~"), "terraform.d", "plugin-cache")

    def get_token(self):
        if os.environ.get(self.token_environment_variable_name) is not None:
            token = os.environ[self.token_environment_variable_name]
            if (os.path.exists(self.config_file)) and (os.stat(self.config_file).st_size != 0):
                with open(self.config_file, 'r') as cf:
                    cf_obj = json.load(cf)
                    cf_obj['credentials']['app.terraform.io']['token'] = token
                with open(self.config_file, 'w') as cf:
                    json.dump(cf_obj, cf, indent = 4, sort_keys=True)
            else:
                console.warn("\n  Config file: " + self.config_file + " is being configured from env variable !", showTime=False)
                with open(self.config_file, 'w') as cf:
                    json_cf = json.loads(json.dumps(self.tfc_config_template))
                    json_cf['credentials']['app.terraform.io']['token'] = token
                    json.dump(json_cf, cf, indent = 4, sort_keys=True)
        elif os.path.exists(self.config_file):
            if os.stat(self.config_file).st_size == 0:
                console.error("  The TFC config file: " + self.config_file + " is empty !", showTime=False)
                sys.exit(2)
            else:
                with open(self.config_file, 'r') as fp:
                    obj = hcl.load(fp)
                    token = obj['credentials']['app.terraform.io']['token']
        else:
            console.error("  Please configure the 'TF_TOKEN' env variable or \n  the '" + self.config_file + "' file \n  to contain the deployment token !\n", showTime=False)
            sys.exit(2)
        return token

    def get_workspaces(self):
        workspace_list = []
        read_workspaces = requests.get(self.workspaces_url, headers = self.tf_headers)
        r_json = read_workspaces.json()
        if read_workspaces.ok:
            for item in r_json['data']:
                workspace_name = item['attributes']['name']
                workspace_list.append(workspace_name)
        else:
            console.error("\n  Your 'tf_cloud_org' variable or your credentials are invalid !", showTime=False)
            console.error("  - Error Code: " + str(read_workspaces.status_code) + "\n  - Error Message: " + r_json['errors'][0]['title'], showTime=False)
            sys.exit(2)
        return workspace_list

    def create_workspace(self, name, tf_version):
        workspace_data = dict(
            attributes={
                'name':name,
                'terraform-version':tf_version,
                'execution-mode':'local'
            }
        )
        workspace_data = dict(
            data=workspace_data
        )
        
        if name not in self.get_workspaces():
            requests.post(self.workspaces_url, headers=self.tf_headers, data=json.dumps(workspace_data))
