########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# Built-in Imports
import os
import shutil
from subprocess import Popen, PIPE

from cloudify import ctx
from cloudify import exceptions

# Third-party Imports
# Cloudify imports
CLOUDIFY_MANAGER_PRIVATE_KEY_PATH = 'CLOUDIFY_MANAGER_PRIVATE_KEY_PATH'

def get_executible_path(executable_name):

    """home = os.path.expanduser("~")
    deployment_home = \
        os.path.join(home, '{}{}'.format('cloudify.', ctx.deployment.id))

    return os.path.join(deployment_home, 'env', 'bin', executible_name)
    """
    return executable_name

def get_roles(roles, target_path):
    
    try:
        path_to_file = ctx.download_resource(roles, os.path.join(target_path, roles))
    except exceptions.HttpException as e:
        raise exceptions.NonRecoverableError(
            'Could not get roles file: {}.'.format(str(e)))

    return path_to_file


def get_playbook_path(playbook, target_path):
    try:
        path_to_file = ctx.download_resource(playbook, os.path.join(target_path, playbook))
    except exceptions.HttpException as e:
        raise exceptions.NonRecoverableError(
            'Could not get playbook file: {}.'.format(str(e)))

    return path_to_file


def get_inventory_path(inventory, target_path):
    path_to_file = os.path.join(target_path, '{}.inventory'.format(ctx.deployment.id))
    
    if not inventory:
        inventory.append(ctx.instance.host_ip)

    with open(path_to_file, 'w') as f:
        for host in inventory:
            f.write('{0}\n'.format(host))

    return path_to_file


def get_agent_user(user=None):

    if not user:
        if 'user' not in ctx.instance.runtime_properties:
            user = ctx.bootstrap_context.cloudify_agent.user
            ctx.instance.runtime_properties['user'] = user
        else:
            user = ctx.instance.runtime_properties['user']
    elif 'user' not in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties['user'] = user

    return user


def get_keypair_path(keypair):

    home = os.path.expanduser("~")
    path_to_file = \
        os.path.join(home, '.ssh', keypair)

    if not os.path.exists(path_to_file):
        raise exceptions.RecoverableError(
            'Keypair file does not exist.')
    
    ansible_home = get_ansible_home()
    target_path = os.path.join(ansible_home, keypair)
    
    if not os.path.exists(ansible_home):
        os.makedirs(ansible_home)
        ctx.logger.info('Created folder for ansible scripts: {}'.format(ansible_home))
    
    if not os.path.isfile(target_path):
        shutil.copy2(path_to_file, target_path)

    return target_path


def write_configuration_file(path, config):

    file_path = os.path.join(path, 'ansible.cfg')

    with open(file_path, 'w') as f:
        f.write(config)

    return file_path


def run_command(command):

    try:
        run = Popen(command, stdout=PIPE)
    except Exception as e:
        raise exceptions.NonRecoverableError(
            'Unable to run command. Error {}'.format(str(e)))

    try:
        output = run.communicate()
    except Exception as e:
        raise exceptions.NonRecoverableError(
            'Unable to run command. Error {}'.format(str(e)))

    if run.returncode != 0:
        raise exceptions.NonRecoverableError(
            'Non-zero returncode. Output {}.'.format(output))

    return output

def get_ansible_home():
    home = os.path.expanduser("~")
    return os.path.join(home, '{}{}'.format('cloudify.', ctx.deployment.id), '{}'.format(ctx.instance.id))

def create_playbook_from_roles(hosts, roles, filename = 'playbook.yaml' , sudo = 'no', path=None):
    
    if path == None:
        path = get_ansible_home()
        
    pb_string = '- hosts:\n'\
    
    for host in hosts:
        pb_string += '  - ' + host + '\n' 
               
    pb_string += '  sudo: ' + sudo + '\n' \
               '  roles:\n'
    
    for role in roles:
        pb_string += '  - ' + role + '\n'
        
        
    with open(os.path.join(path, filename), 'w') as f:
        f.write('{0}\n'.format(pb_string))

    f.close()
    
    return os.path.join(path, filename)
    
    
    



