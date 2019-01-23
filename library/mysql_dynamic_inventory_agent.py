#!/usr/bin/env python

# Copyright: (c) 2018, Larry Smith <mrlesmithjr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule
import mysql.connector
# from mysql.connector import Error
# import socket

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        ansible_groups=dict(type='list', required=False),
        ansible_host=dict(type='str', required=True),
        ansible_hostname=dict(type='str', required=True),
        dbhost=dict(type='str', required=True),
        dbname=dict(type='str', required=False, default='ansible'),
        dbpass=dict(type='str', required=True, no_log=True),
        dbport=dict(type='str', required=False, default='3306'),
        dbuser=dict(type='str', required=True)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    connection = mysql.connector.connect(
        host=module.params['dbhost'],
        user=module.params['dbuser'],
        passwd=module.params['dbuser'],
        database=module.params['dbname'],
        port=module.params['dbport'])
    cursor = connection.cursor()
    # hostname = socket.getfqdn()
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.connect(("8.8.8.8", 80))
    # ip_address = (s.getsockname()[0])
    # s.close()
    sql = "SELECT id FROM hosts WHERE name='{0}'".format(
        module.params['ansible_hostname'])
    cursor.execute(sql)
    hostname_check = cursor.fetchone()
    if hostname_check is None:
        sql = "INSERT INTO hosts(name) VALUES('{0}')".format(
            module.params['ansible_hostname'])
        cursor.execute(sql)
        result['changed'] = True
    sql = ("SELECT value FROM hostvars "
           "WHERE name='ansible_host' "
           "AND "
           "hostid=(SELECT id FROM hosts WHERE name='{0}')".format(
               module.params['ansible_hostname']))
    cursor.execute(sql)
    ansible_hostname_check = cursor.fetchone()
    update_ansible_hostname = False
    if ansible_hostname_check is None:
        update_ansible_hostname = True
    elif ansible_hostname_check[0] != module.params['ansible_host']:
        update_ansible_hostname = True
    if update_ansible_hostname:
        sql = ("REPLACE INTO hostvars(name, value, hostid) "
               "VALUES('ansible_host', '{0}', "
               "(SELECT id FROM hosts WHERE name='{1}'))".format(module.params[
                   'ansible_host'], module.params['ansible_hostname']))
        cursor.execute(sql)
        result['changed'] = True
    for group in module.params['ansible_groups']:
        sql = "SELECT id FROM groups WHERE name='{0}'".format(group)
        cursor.execute(sql)
        group_check = cursor.fetchone()
        if group_check is None:
            sql = "INSERT IGNORE INTO groups(name) VALUES('{0}')".format(group)
            cursor.execute(sql)
            result['changed'] = True
        sql = ("SELECT a.name FROM groups a "
               "INNER JOIN hostgroups b "
               "ON a.id=b.groupid "
               "INNER JOIN hosts c "
               "ON b.hostid=c.id "
               "WHERE c.name='{0}'".format(module.params['ansible_hostname']))
        cursor.execute(sql)
        host_groups = []
        for row in cursor.fetchall():
            host_groups.append(row[0])
        if group not in host_groups:
            sql = ("INSERT INTO hostgroups(hostid, groupid) "
                   "VALUES((SELECT id FROM hosts WHERE name='{0}'), "
                   "(SELECT id FROM groups WHERE name='{1}'))".format(
                       module.params['ansible_hostname'], group))
            cursor.execute(sql)
            result['changed'] = True
    connection.commit()
    cursor.close()

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    # result['original_message'] = module.params['name']
    # result['message'] = 'goodbye'

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    # if module.params['new']:
    #     result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    # if module.params['name'] == 'fail me':
    #     module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()