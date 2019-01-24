#!/usr/bin/env python
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        module_args = self._task.args.copy()
        module_args['ansible_groups'] = self._templar._available_variables.get(
            'group_names')
        module_args['ansible_host'] = self._templar._available_variables.get(
            'ansible_host')
        module_args['ansible_hostname'] = self._templar._available_variables.get(
            'inventory_hostname')
        module_args['guest_os'] = self._templar._available_variables.get(
            'ansible_os_family')
        return self._execute_module(module_args=module_args,
                                    task_vars=task_vars, tmp=tmp)
