"""
Copyright 2017 BlazeMeter Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import traceback
import os

from subprocess import CalledProcessError, check_output, STDOUT

from bzt import TaurusConfigError
from bzt.modules import SubprocessedExecutor
from bzt.engine import HavingInstallableTools
from bzt.utils import RequiredTool, is_windows, TclLibrary, RESOURCES_DIR


class RSpecTester(SubprocessedExecutor, HavingInstallableTools):
    """
    RSpec tests runner
    """

    def __init__(self):
        super(RSpecTester, self).__init__()
        self.plugin = None
        self.script = None

    def prepare(self):
        super(RSpecTester, self).prepare()
        self.install_required_tools()
        self.script = self.get_script_path()
        if not self.script:
            raise TaurusConfigError("Script not passed to runner %s" % self)

        self.reporting_setup(suffix='.ldjson')

    def install_required_tools(self):
        self.plugin = self._get_tool(TaurusRSpecPlugin)

        tools = [self._get_tool(TclLibrary),
                 self._get_tool(Ruby, config=self.settings),
                 self._get_tool(RSpec),
                 self.plugin]
        self._check_tools(tools)

    def startup(self):
        """
        run rspec plugin
        """
        interpreter = self.settings.get("interpreter", "ruby")

        rspec_cmdline = [
            interpreter,
            self.plugin.tool_path,
            "--report-file",
            self.report_file,
            "--test-suite",
            self.script
        ]
        load = self.get_load()
        if load.iterations:
            rspec_cmdline += ['--iterations', str(load.iterations)]

        if load.hold:
            rspec_cmdline += ['--hold-for', str(load.hold)]

        self._start_subprocess(rspec_cmdline)


class Ruby(RequiredTool):
    def __init__(self, config=None, **kwargs):
        settings = config or {}
        tool_path = settings.get("interpreter", "ruby")
        super(Ruby, self).__init__(tool_path=tool_path, installable=False, **kwargs)

    def check_if_installed(self):
        try:
            output = check_output([self.tool_path, '--version'], stderr=STDOUT)
            self.log.debug("%s output: %s", self.tool_name, output)
            return True
        except (CalledProcessError, OSError):
            return False


class RSpec(RequiredTool):
    def __init__(self, **kwargs):
        super(RSpec, self).__init__(installable=False, **kwargs)

    def check_if_installed(self):
        try:
            rspec_exec = "rspec.bat" if is_windows() else "rspec"
            output = check_output([rspec_exec, '--version'], stderr=STDOUT)
            self.log.debug("%s output: %s", self.tool_name, output)
            return True
        except (CalledProcessError, OSError):
            self.log.debug("RSpec check exception: %s", traceback.format_exc())
            return False


class TaurusRSpecPlugin(RequiredTool):
    def __init__(self, **kwargs):
        tool_path = os.path.join(RESOURCES_DIR, "rspec_taurus_plugin.rb")
        super(TaurusRSpecPlugin, self).__init__(tool_path=tool_path, installable=False, **kwargs)
