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
        self.org_url = self.base_url + '/api/v2/organizations/' + self.org
        self.workspaces_url = self.org_url + '/workspaces'
        self.token_environment_variable_name = "TF_TOKEN"
        self.get_terraformrc_path()
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
        else:
            self.config_file = os.path.join(os.path.expanduser("~"), ".terraformrc")

    def get_token(self):
        if os.environ.get(self.token_environment_variable_name) is not None:
            token = os.environ[self.token_environment_variable_name]
        elif os.path.exists(self.config_file):
            with open(self.config_file, 'r') as fp:
                obj = hcl.load(fp)
                token = obj['credentials']['app.terraform.io']['token']
        return token

    def get_workspaces(self):
        workspace_list = []
        read_workspaces = requests.get(self.workspaces_url, headers = self.tf_headers)
        r_json = read_workspaces.json()

        for item in r_json['data']:
            workspace_name = item['attributes']['name']
            workspace_list.append(workspace_name)
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
