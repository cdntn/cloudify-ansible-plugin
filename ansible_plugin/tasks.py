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

from cloudify import ctx
from cloudify.decorators import operation

from ansible_plugin import utils
from context import CloudifyContext

ctx = ctx()
assert isinstance(ctx, CloudifyContext)

# Third-party Imports
# Cloudify imports
@operation
def configure(user, keypair, playbook, roles, private_ip_address, **kwargs):    
    assert isinstance(ctx, CloudifyContext)
    
    ctx.logger.info('Configuring Ansible.')
    
    os.environ['USER'] = user
    os.environ['HOME'] = os.path.expanduser("~")
    
    ansible_home = utils.get_ansible_home()
    
    if not os.path.exists(ansible_home):
        os.makedirs(ansible_home)
        ctx.logger.info('Created folder for ansible scripts: {}'.format(ansible_home))

    ctx.logger.info('Getting the path to the keypair.')
    path_to_key = utils.get_keypair_path(keypair)
    os.chmod(path_to_key, 0600)
    ctx.logger.info('Got the keypair path: {}'.format(path_to_key))

        
    configuration = '[defaults]\n' \
                    'host_key_checking=False\n' \
            'remote_user={0}\n'\
                    'private_key_file={1}\n'\
                    '[ssh_connection]\n'\
                    'control_path=%(directory)s/%%h-%%r\n'.format(user, path_to_key)
    
    file_path = utils.write_configuration_file(ansible_home, configuration)
    os.environ['ANSIBLE_CONFIG'] = file_path
    
    ctx.logger.info('Getting the path to the playbook.')
    playbook_path = utils.get_playbook_path(playbook, ansible_home)
    ctx.logger.info('Got the playbook path: {}.'.format(playbook_path))
    
    ctx.logger.info('Upload the roles file.')
    roles_path = utils.get_roles(roles, ansible_home)
    ctx.logger.info('Got the roles path: {}'.format(roles_path))
    
    ctx.logger.info('Unzip the roles file.')
    command = ['unzip', '-o', roles_path,'-d', os.path.dirname(roles_path)] 
    ctx.logger.info('Running command: {}.'.format(command))
    output = utils.run_command(command)
    ctx.logger.info('Command Output: {}.'.format(output))
    
    """ctx.logger.info('Delete the roles archive.')
    os.remove(roles_path)
    command = ['rm', '-rf', roles_path]
    ctx.logger.info('Running command: {}.'.format(command))
    output = utils.run_command(command)
    ctx.logger.info('Command Output: {}.'.format(output))
    """
    ctx.logger.info('Getting the inventory path.')
    ips = [private_ip_address]
    inventory_path = utils.get_inventory_path(ips, os.path.dirname(playbook_path))
    ctx.logger.info('Got the inventory path: {}.'.format(inventory_path))
    
    ctx.logger.info('Configured Ansible.')


@operation
def ansible_playbook(playbook, **kwargs):
    cur_ctx = ctx()
    assert isinstance(cur_ctx, CloudifyContext)
    
    """ Runs a playbook as part of a Cloudify lifecycle operation """
    ansible_home = utils.get_ansible_home()

    executible = utils.get_executible_path('ansible-playbook')
    inventory_path = os.path.join(ansible_home, '{}.inventory'.format(cur_ctx.deployment.id))
    playbook_path = os.path.join(ansible_home, playbook)
    
    os.environ['HOME'] = ansible_home
    os.environ['ANSIBLE_CONFIG'] = os.path.join(ansible_home, 'ansible.cfg')
    
    command = [executible, '-i', inventory_path,
               playbook_path, '--timeout=60', '-vvvv']

    cur_ctx.logger.info('Running command: {}.'.format(command))

    output = utils.run_command(command)

    cur_ctx.logger.info('Command Output: {}.'.format(output))

    cur_ctx.logger.info('Finished running the Ansible Playbook.')
    
    del os.environ['HOME']
    
