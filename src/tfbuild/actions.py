#!/usr/bin/python3 -u

from .core import Core
from .workspace import Workspace
from py_console import console
import json
import jsonpickle
import os
import pkg_resources
import sys
import shutil, stat
import subprocess

class Action(Core):
    """
    Inherits the Base Class and its attributes.
    Adding in 2 child atts, action, and target_environment.
    """
    def __init__(self, action, target_environment):
        self.action = action
        self.target_environment = target_environment
        Core.__init__(self, action, target_environment)

    def __str__(self):
        return ' '.join((self.repo_name, self.location))

    def command(self, command):
        """
        Re-usable function to execute a shell command, 
        with error handling, and ability to execute quietly, 
        or display output.
        """
        output = subprocess.Popen(command, env=self.my_env)
        output.communicate()
        
    def apply(self):
        self.init()
        console.success("  Running Terraform Apply", showTime=False)
        self.command("terraform apply{}".format(self.var_file_args).split())

    def applynoprompt(self):
        self.reinit()
        console.success("  Running Terraform Apply", showTime=False)
        self.command("terraform apply -input=false -auto-approve{}".format(self.var_file_args).split())

    def destroy(self):
        """
        Force Destroy on Terraform, based on site, and resources.
        """
        self.init()
        console.success("  Running Terraform Destroy", showTime=False)
        self.command("terraform destroy{}".format(self.var_file_args).split())

    def destroyforce(self):
        """
        Force Destroy on Terraform, based on site, and resources.
        """
        self.reinit()
        console.success("  Running Terraform Destroy Force", showTime=False)
        self.command("terraform destroy -force{}".format(self.var_file_args).split())

    def help(self):
        """
        Provide Application Help
        """
        help = """
        Usage:
           {0} <command>
           {0} <command>-<site>

        Example:
           {0} plan
           {0} plan-dr

        Commands:
           apply          Apply Terraform configuration
           destroy        Destroy Terraform Configuration
           destroyforce   Destroy Terraform Configuration with no prompt
           help           Display the help menu that shows available commands
           init           Initialize Terraform backend and clean local cache
           plan           Create Terraform plan with clean local cache
           plandestroy    Create a Plan for a Destroy scenario
           reinit         Initialize Terraform backend and keep local cache
           replan         Create Terraform plan with existing local cache
           taint          Taint specific module and resources
           test           Test run showing all project variables
           tfimport       Import states for existing resources
           update         Update Terraform modules
           version        App version
        """
        print(help.format(self.app_name))

    def init(self):
        """
        Initialize the terraform backend using the appropriate env,
        and variables.
        """
        console.success("  Initializing Terraform", showTime=False)
        if os.path.exists('.terraform'):
            console.success("  Removing .terraform", showTime=False)
            def del_rw(action, name, exc):
                os.chmod(name, stat.S_IWRITE)
                os.remove(name)
            shutil.rmtree('.terraform', onerror=del_rw)
        self.reinit()

    def plan(self):
        self.init()
        console.success("  Creating a Terraform Plan", showTime=False)
        self.command("terraform plan{}".format(self.var_file_args).split())

    def plandestroy(self):
        self.init()
        console.success("  Creating a Destroy Plan", showTime=False)
        self.command("terraform plan -input=false -refresh=true -destroy{}".format(self.var_file_args).split())

    def refresh(self):
        self.command("terraform refresh{}".format(self.var_file_args).split())

    def reinit(self):
        """
        Initialize the terraform backend using the appropriate env,
        and variables.
        """
        if self.cloud == "aws":
            console.success("  Initializing AWS Backend", showTime=False)
            self.command(
                [
                    'terraform', 'init',
                    '-backend-config', 'region='+self.backend_region,
                    '-backend-config', 'bucket='+self.bucket,
                    '-backend-config', 'key='+self.bucket_key
                    ]
                ) 
        elif self.cloud == "azr":
            console.success("  Initializing AZR Backend", showTime=False)
            self.command(
                [
                    'terraform', 'init',
                    '-backend-config', 'storage_account_name='+self.bucket, 
                    '-backend-config', 'container_name='+self.account+'1', 
                    '-backend-config', 'key='+self.bucket_key, 
                    '-backend-config', self.secret_path
                    ]
                )
        elif self.tf_cloud_backend == "true":
            console.success("  Initializing Terraform Clound Backend", showTime=False)
            Workspace(self.bucket_key, self.platform, self.version_tf(), self.tf_cloud_backend_org)
            if not os.path.exists('.terraform'):
                console.success("  Creating .terraform directory and backend configuration", showTime=False)
                os.makedirs('.terraform')
                backend_config = '.terraform/backend-'+self.environment+'.hcl'
                with open(backend_config, 'w') as config_object:
                    config_object.write('workspaces { name = \"'+self.bucket_key+'" }')
            self.command(
                [
                    'terraform', 'init',
                    '-backend-config', 'organization='+self.account, 
                    '-backend-config', '.terraform/backend-'+self.environment+'.hcl'
                    ]
                )
        else:
            console.success("  Initializing Terraform Local Backend", showTime=False)
            self.command(
                [
                    'terraform', 'init'
                    ]
                )

    def replan(self):
        self.reinit()
        console.success("  Running Terraform Plan", showTime=False)
        self.command("terraform plan{}".format(self.var_file_args).split())

    def taintresources(self):
        """
        Create Taint resources list.
        """
        console.success("  Running Terraform Resource Query", showTime=False)
        modules = []
        resources = []
        show_cmd = subprocess.Popen(['terraform', 'show'],stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout, stderr) = show_cmd.communicate()
        lines = stdout.strip().decode().replace(":","").splitlines()
        for line in lines:
            if "module" in line:
                items = line.split(".")
                if len(items) > 1:
                    module = items[1]
                    if module not in modules:
                        modules.append(module)
       
        if len(modules) > 1:
            i = 0
            print("Please choose the module you would like to taint:")
            for module in modules:
                print('[', i, ']: ', module)
                i += 1
            selectedmoduleindex = input("Module Selection: ")
            if int(selectedmoduleindex) > (len(modules) - 1):
                print('You selected an invalid module index, please try again')
                sys.exit(0)
        
            selected_module = modules[int(selectedmoduleindex)]
            print(selected_module)
        
        for line in lines:
            if selected_module in line:
                items = line.split(".")
                if len(items) > 1:
                    resource = items[2]
                    if resource not in resources:
                        resources.append(resource)
    
        if len(resources) > 1:
            i = 0
            print("Please choose the resource you would like to taint:")
            for resource in resources:
                print('[', i, ']: ', resource)
                i += 1
            selectedresourceindex = input("Resource Selection: ")
            if int(selectedresourceindex) > (len(resources) - 1):
                print('You selected an invalid resource index, please try again')
                sys.exit(0)
        
            selected_resource = resources[int(selectedresourceindex)]
            print(selected_resource)
            return selected_module, selected_resource

    def taint(self):
        """
        Taint resources.
        """
        self.init()
        modules_totaint = []
        resources_totaint = []
        console.success("  Running Terraform Taint", showTime=False)
        taintagain = 'y'

        while taintagain == 'y':
            taintresources = self.taintresources()
            modules_totaint.append(taintresources[0])
            resources_totaint.append(taintresources[1])
            taintagain = input("Select another module to taint? [y/n] : ")

        print('Tainting the following resources:')
        if len(modules_totaint) >= 1:
            i = 0
            for i in range(len(modules_totaint)):
                print('[', i, ']: [', modules_totaint[i], '] ', resources_totaint[i])
                i += 1

        gotaint = input("Proceed with Taint? [y/n] : ")
        
        if gotaint == 'y':
            if len(modules_totaint) >= 1:
                i = 0
                for i in range(len(modules_totaint)):
                    self.command(
                        [
                            'echo', 'taint',
                            '-var-file='+self.common_env_file,
                            '-var-file='+self.local_env_file,
                            '-module', modules_totaint[i], resources_totaint[i]
                            ]
                        ) 
                    i += 1

    def test(self):
        """
        Test all class attributes through a single cli call. 
        """
        console.warn("  Terraform Prerequisites Check", showTime=False)
        console.warn("  =============================", showTime=False)
        self.version_git()
        self.version_tf()

        serialized = json.loads(jsonpickle.encode(self, max_depth=2))

        console.warn("  Current Deployment Details", showTime=False)
        console.warn("  ==========================", showTime=False)
        console.success("  Platform           = {platform}".format(**serialized), showTime=False)
        console.success("  AppDir             = {location}".format(**serialized), showTime=False)
        console.success("  Repo Name          = {repo_name}".format(**serialized), showTime=False)
        console.success("  Repo Root          = {repo_root}".format(**serialized), showTime=False)
        console.success("  Repo URL           = {repo_url}".format(**serialized), showTime=False)
        console.success("  Branch Name        = {branch_name}".format(**serialized), showTime=False)
        console.success("  Resource Name      = {resource}".format(**serialized), showTime=False)
        console.success("  Cloud              = {cloud}".format(**serialized), showTime=False)
        console.success("  Project            = {project}".format(**serialized), showTime=False)
        console.success("  Account            = {account}".format(**serialized), showTime=False)
        console.success("  Environment        = {environment}".format(**serialized), showTime=False)
        console.success("  Common Shell File  = {common_shell_file}".format(**serialized), showTime=False)
        console.success("  Common Env File    = {common_env_file}".format(**serialized), showTime=False)
        console.success("  Local Env File     = {local_env_file}".format(**serialized), showTime=False)
        console.success("  Site (Target Env.) = {site}".format(**serialized), showTime=False)
        console.success("  Command            = {action}".format(**serialized), showTime=False)
        console.success("  DR                 = {dr}".format(**serialized), showTime=False)
        console.success("  Prefix             = {prefix}".format(**serialized), showTime=False)
        console.success("  Module             = {module}".format(**serialized), showTime=False)
        console.success("  Backend Secret     = {secret_path}".format(**serialized), showTime=False)
        console.success("  Deployment Region  = {region}".format(**serialized), showTime=False)
        console.success("  Backend Region     = {backend_region}".format(**serialized), showTime=False)
        console.success("  Bucket             = {bucket}".format(**serialized), showTime=False)
        console.success("  Key                = {bucket_key}".format(**serialized), showTime=False)
        console.success("  China Deployment   = {china_deployment}".format(**serialized), showTime=False)
        print("")
        console.warn("  Terraform Variables", showTime=False)
        console.warn("  ===================", showTime=False)
        console.success("  TF_VAR_mode             = {mode}".format(**serialized), showTime=False)
        console.success("  TF_VAR_project          = {project}".format(**serialized), showTime=False)
        console.success("  TF_VAR_account          = {account}".format(**serialized), showTime=False)
        console.success("  TF_VAR_env              = {environment}".format(**serialized), showTime=False)
        console.success("  TF_VAR_azrsa            = {bucket}".format(**serialized), showTime=False)
        console.success("  TF_VAR_bucket           = {bucket}".format(**serialized), showTime=False)
        console.success("  TF_VAR_prefix           = {prefix}".format(**serialized), showTime=False)
        console.success("  TF_CLI_ARGS             = {tf_cli_args}".format(**serialized), showTime=False)
        console.success("  TF_VAR_china_deployment = {china_deployment}".format(**serialized), showTime=False)

    def tfimport(self):
        self.init()
        console.success("  Running Terraform Import", showTime=False)
        self.command("terraform import{}".format(self.var_file_args).split())

    def update(self):
        console.success("  Updating Modules", showTime=False)
        self.command("terraform get -update=true{}".format(self.var_file_args).split())

    def version(self):
        """
        Get application version from VERSION with cli call.
        """
        version = pkg_resources.require(self.app_name)[0].version
        console.success("  " + self.app_name.upper() + " version: " + version, showTime=False)

    def version_git(self):
        """
        Get the version of Git used.
        """
        try:    
            show_cmd = subprocess.Popen(['git', '--version'],stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout, stderr) = show_cmd.communicate()
            git_version = stdout.strip().decode().split(" ")[2]
            console.success("  Git version: " + git_version, showTime=False)
        except:
            console.error("  Git is not installed", showTime=False)
            sys.exit(2)  

        return git_version

    def version_tf(self):
        """
        Get the version of Terraform used.
        """
        try:
            show_cmd = subprocess.Popen(['terraform', 'version', '-json'],stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (stdout, stderr) = show_cmd.communicate()
            output = json.loads(stdout)
            terraform_version = output['terraform_version']
            console.success("  Terraform version: " + terraform_version, showTime=False)
        except:
            console.error("  Terraform is not installed", showTime=False)
            sys.exit(2)  

        return terraform_version

