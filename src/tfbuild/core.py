#!/usr/bin/python3 -u

from git import Repo
from py_console import console
import confuse
import hcl
import os
import sys

class Core():
    def __init__(self, action, target_environment=None):
        self.get_platform()
        self.app_name = os.path.basename(sys.argv[0])
        self.app_config = os.path.basename(os.path.dirname(__file__))
        self.action = action
        self.build_id = os.getenv('BUILD_ID')
        self.target_environment = target_environment
        self.location = os.path.realpath(os.getcwd())
        self.repo_url = Repo(self.repo_root).remotes[0].config_reader.get("url")
        self.repo_name = str(os.path.splitext(os.path.basename(self.repo_url))[0])
        self.branch_name = str(Repo(self.repo_root).active_branch)
        self.clouds_list = ['aws', 'azr', 'vmw', 'gcp']
        self.bucket_prefix = self.load_configs()['bucket_prefix'].get(confuse.Optional(str, default='inf.tfstate'))
        self.tf_cloud_org1 = self.load_configs()['tf_cloud_org'].get(confuse.Optional(str, default=None))
        self.cloud = self.repo_name.split("-")[0]
        self.resource = os.path.relpath(self.location, self.repo_root).replace('\\', '/')
        self.config_files = self.load_configs()
        self.get_default_variables()
        self.secret_path = os.path.join("{}".format(self.repo_root), "secret_{}_backend.tfvars".format(self.cloud))
        self.get_env_files()
        self.get_deployment_attributes()
        self.sanity_check()
        self.get_backend_configuration()
        self.export_environment()

    def get_platform(self):
        repo_root = Repo(search_parent_directories=True).git.rev_parse("--show-toplevel")
        if sys.platform.startswith("win"):
            self.platform = "windows"
            self.repo_root = repo_root.replace('/', '\\')
        else:
            self.platform = "linux"
            self.repo_root = repo_root

    def load_configs(self):
        config = confuse.LazyConfig(self.app_config, __name__)
        #config._add_default_source()
        #config_file = os.path.join(self.location, 'config_default.yaml')
        #config.set_file(config_file)
        if os.path.isfile(config.user_config_path()):
            config.set_file(config.user_config_path(), base_for_paths=True)
        return config

    def get_default_variables(self):
        """
        Get Cloud Dependent Project, Account, Environment variables.
        """
        if self.cloud in self.clouds_list:
            self.project = self.repo_name.split("-")[1]
            self.account = self.branch_name.split("-")[0]
            self.environment = self.branch_name.split("-")[1]
        else:
            self.project = self.repo_name.split("-")[1]
            self.account = 'none'
            self.environment = self.branch_name

    def get_env_files(self):
        """
        Return Appropriate Env File Based on whether there is
        a target deployment defined in the init attributes.
        """
        if self.target_environment:
            file_preffix = "{}_{}".format(self.environment, self.target_environment)
        else:
            file_preffix = "{}".format(self.environment)
        
        self.common_shell_file = os.path.join(
            self.repo_root, "common", "environments","env_{}.hcl".format(file_preffix))
        self.common_env_file = os.path.join(
            self.repo_root, "common", "environments","env_{}_common.tfvars".format(file_preffix))
        self.local_env_file = os.path.join(
            self.location, "environments", "env_{}.tfvars".format(file_preffix))

    def get_deployment_attributes(self):
        """
        Extract deployment attributes from shell env file.
        This is done to maintain backward compatibility with
        current deployments, but should be migrated to a declarative
        language in the future, ie: json,yaml.
        """

        if not os.path.isfile(self.common_shell_file):
            console.error("  No Common Wrapper Shell File available ! Please create:\n  " + self.common_shell_file + "\n  and add configuration content if necessary !\n", showTime=False)
            sys.exit(2)

        try:    
            with open(self.common_shell_file, 'r') as fp:
                obj = hcl.load(fp)
                self.china_deployment = obj.get('china_deployment', '')
                self.dr = obj.get('dr', '')
                self.global_resource = obj.get('global_resource', '')
                self.mode = obj.get('mode', '')
                self.region = obj.get('region', '')
                self.tf_cloud_backend = obj.get('tf_cloud_backend', '')               
                self.tf_cloud_org2 = obj.get('tf_cloud_org', '')               
                if sys.platform.startswith("win"):
                    self.tf_cli_args = obj.get('tf_cli_args', '').replace('"','').replace('${REPO_PATH}',self.repo_root).replace('$REPO_PATH',self.repo_root).replace('\\', '\\\\').replace('/', '\\\\')
                else:
                    self.tf_cli_args = obj.get('tf_cli_args', '').replace('"','').replace('${REPO_PATH}',self.repo_root).replace('$REPO_PATH',self.repo_root)
        except KeyError:
            console.error("  Missing Common Shell Env File: \n          {}\n".format(self.common_shell_file), showTime=False)
            sys.exit(2)
        except(ValueError):
            pass   

    def sanity_check(self):
        """
        Series of sanity Checks performed to ensure what we
        are working with.
        """

        self.var_file_args_list = []
        self.var_file_args = ''

        if os.path.isfile(self.secret_path):
            self.var_file_args_list.append(self.secret_path)

        if self.location == self.repo_root:
            console.error("  You are executing " + self.app_name.upper() + " from the repository root !\n          Please ensure execution from a resurce directory !\n", showTime=False)
            sys.exit(2)

        if not os.path.isfile(self.local_env_file):
            console.error("  No Local Environment Files at this location !\n", showTime=False)
            if not any(File.endswith(".tf") for File in os.listdir(self.location)):
                console.error("  You are executing " + self.app_name.upper() + " from an improper location,\n          Please ensure execution from a resurce directory !\n", showTime=False)
                sys.exit(2)
            else:
                console.error("  Please create:\n          " + self.local_env_file + "\n          and add configuration content if necessary !\n", showTime=False)
                sys.exit(2)
        else:
            self.var_file_args_list.append(self.local_env_file)

        if not os.path.isfile(self.common_env_file):
            console.success("  No Common Environment File available ! Please create:\n            " + self.common_env_file + "\n            and add configuration content if necessary !\n", showTime=False)
            #sys.exit(2)
        else:
            self.var_file_args_list.append(self.common_env_file)

        if not self.region:
            if self.cloud in ['aws', 'azr']:
                console.error("  Specify 'region' in the file: \n          " + self.common_shell_file, showTime=False)
                sys.exit(2)

        for env_file in self.var_file_args_list:
            self.var_file_args += ' -var-file=' + env_file

    def get_backend_configuration(self):
        """
        Parse Data returned by get_deployment_attributes and
        return bucket, backend_region for deployment.
        """

        if self.target_environment:
            self.site = self.target_environment
            if self.mode == "true":
                self.prefix = "{}-{}-{}".format(self.project, self.target_environment, self.mode)
                self.module = "{}-{}".format(self.resource, self.mode)
            else:
                self.prefix = "{}-{}".format(self.project, self.target_environment)
                self.module = self.resource
        else:
            self.site = ''
            if self.mode == "true":
                self.prefix = "{}-{}".format(self.project, self.mode)
                self.module = "{}-{}".format(self.resource, self.mode)
            else:
                self.prefix = self.project
                self.module = self.resource

        if self.cloud == "aws":
            if self.global_resource == "True" or self.resource.__contains__("53") == True:
                self.bucket_key = "{prefix}/{module}/terraform.tfstate".format(
                    prefix=self.prefix,
                    module=self.module
                )            
            else:
                self.bucket_key = "{prefix}/{region}/{module}/terraform.tfstate".format(
                    prefix=self.prefix,
                    region=self.region,
                    module=self.module
                )

            if self.dr == "true":
                self.bucket = "{}.{}.{}.dr".format(self.bucket_prefix, self.account, self.environment)
                if self.china_deployment == "true":
                    self.backend_region = "cn-northwest-1"
                else:
                    self.backend_region = "us-west-2"
            else:   
                self.bucket = "{}.{}.{}".format(self.bucket_prefix, self.account, self.environment)
                if self.china_deployment == "true":
                    self.backend_region = "cn-north-1"
                else:
                    self.backend_region = "us-east-1"
        elif self.cloud == "azr":
            self.bucket_key = "{env}/{prefix}/{region}/{module}/terraform.tfstate".format(
                env=self.environment,
                prefix=self.prefix,
                region=self.region,
                module=self.module
            )                

            if self.dr == "true":
                self.bucket = "{}{}{}dr".format(self.bucket_prefix, self.account, self.environment)
            else:
                self.bucket = "{}{}{}".format(self.bucket_prefix, self.account, self.environment)
        elif (self.cloud not in ['aws', 'azr', 'gcp']) and (self.tf_cloud_backend == "true"):
            self.bucket_key = "{env}-{prefix}-{module}".format(
                env=self.environment,
                prefix=self.prefix.replace("/","-"),
                module=self.module.replace("/","-")
            )
            if self.tf_cloud_org1:
                self.tf_cloud_backend_org = self.tf_cloud_org1
            else:
                self.tf_cloud_backend_org = self.tf_cloud_org2
            self.backend_region = "none"
            self.bucket = "none"
        else:
            self.bucket_key = "none"
            self.backend_region = "none"
            self.bucket = "none"

    def export_environment(self):
        """
        Export the environemt Variables to be used by
        Terraform.
        """
        
        self.my_env = dict(os.environ, 
            **{"TF_VAR_deployment_region": self.region},
            **{"TF_VAR_backend_region": self.backend_region},
            **{"TF_VAR_project": self.project},
            **{"TF_VAR_account": self.account},
            **{"TF_VAR_mode": self.mode},
            **{"TF_VAR_env": self.environment},
            **{"TF_VAR_site": self.site},
            **{"TF_VAR_azrsa": self.bucket},
            **{"TF_VAR_bucket": self.bucket},
            **{"TF_VAR_prefix": self.prefix},
            **{"TF_VAR_china_deployment": self.china_deployment},
            **{"TF_CLI_ARGS": self.tf_cli_args},
            **{"AWS_REGION": self.region},
            **{"AZR_REGION": self.region},
            **{"REPO_PATH": self.repo_root},
            )
