
from __future__ import absolute_import

import os
import signal
import subprocess
import sys

from six import print_

from ccmlib import common
from ccmlib.cmds.command import Cmd
from ccmlib.node import NodeError

NODE_CMDS = [
    "show",
    "remove",
    "showlog",
    "setlog",
    "start",
    "stop",
    "ring",
    "flush",
    "compact",
    "drain",
    "cleanup",
    "repair",
    "scrub",
    "verify",
    "shuffle",
    "sstablesplit",
    "getsstables",
    "decommission",
    "json",
    "updateconf",
    "updatelog4j",
    "stress",
    "cli",
    "cqlsh",
    "scrub",
    "verify",
    "status",
    "setdir",
    "bulkload",
    "version",
    "nodetool",
    "dsetool",
    "setworkload",
    "dse",
    "hadoop",
    "hive",
    "pig",
    "sqoop",
    "spark",
    "pause",
    "resume",
    "jconsole",
    "versionfrombuild",
    "byteman"
]


def node_cmds():
    return NODE_CMDS


class NodeShowCmd(Cmd):

    def description(self):
        return "Display information on a node"

    def get_parser(self):
        usage = "usage: ccm node_name show [options]"
        return self._get_default_parser(usage, self.description())

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        self.node.show()


class NodeRemoveCmd(Cmd):

    def description(self):
        return "Remove a node (stopping it if necessary and deleting all its data)"

    def get_parser(self):
        usage = "usage: ccm node_name remove [options]"
        return self._get_default_parser(usage, self.description())

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        self.cluster.remove(self.node)


class NodeShowlogCmd(Cmd):

    def description(self):
        return "Show the log of node name (runs your $PAGER on its system.log)"

    def get_parser(self):
        usage = "usage: ccm node_name showlog [options]"
        return self._get_default_parser(usage, self.description())

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        log = self.node.logfilename()
        pager = os.environ.get('PAGER', common.platform_pager())
        os.execvp(pager, (pager, log))


class NodeSetlogCmd(Cmd):

    def description(self):
        return "Set node name log level (INFO, DEBUG, ...) with/without Java class - require a node restart"

    def get_parser(self):
        usage = "usage: ccm node_name setlog [options] level"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('-c', '--class', type="string", dest="class_name", default=None,
                          help="Optional java class/package. Logging will be set for only this class/package if set")
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        if len(args) == 1:
            print_('Missing log level', file=sys.stderr)
            parser.print_help()
        self.level = args[1]

        try:
            self.class_name = options.class_name
        except common.ArgumentError as e:
            print_(str(e), file=sys.stderr)
            exit(1)

    def run(self):
        try:
            self.node.set_log_level(self.level, self.class_name)

        except common.ArgumentError as e:
            print_(str(e), file=sys.stderr)
            exit(1)


class NodeClearCmd(Cmd):

    def description(self):
        return "Clear the node data & logs (and stop the node)"

    def get_parser(self):
        usage = "usage: ccm node_name_clear [options]"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('-a', '--all', action="store_true", dest="all",
                          help="Also clear the saved cache and node log files", default=False)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        self.node.stop()
        self.node.clear(self.options.all)


class NodeStartCmd(Cmd):

    def description(self):
        return "Start a node"

    def get_parser(self):
        usage = "usage: ccm node start [options] name"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('-v', '--verbose', action="store_true", dest="verbose",
                          help="Print standard output of cassandra process", default=False)
        parser.add_option('--no-wait', action="store_true", dest="no_wait",
                          help="Do not wait for cassandra node to be ready", default=False)
        parser.add_option('--wait-other-notice', action="store_true", dest="deprecate",
                          help="DEPRECATED/IGNORED: Use '--skip-wait-other-notice' instead. This is now on by default.", default=False)
        parser.add_option('--skip-wait-other-notice', action="store_false", dest="wait_other_notice",
                          help="Skip waiting until all live nodes of the cluster have marked the other nodes UP", default=True)
        parser.add_option('--wait-for-binary-proto', action="store_true", dest="wait_for_binary_proto",
                          help="Wait for the binary protocol to start", default=False)
        parser.add_option('-j', '--dont-join-ring', action="store_true", dest="no_join_ring",
                          help="Launch the instance without joining the ring", default=False)
        parser.add_option('--replace-address', type="string", dest="replace_address", default=None,
                          help="Replace a node in the ring through the cassandra.replace_address option")
        parser.add_option('--jvm_arg', action="append", dest="jvm_args",
                          help="Specify a JVM argument", default=[])
        parser.add_option('--quiet-windows', action="store_true", dest="quiet_start", help="Pass -q on Windows 2.2.4+ and 3.0+ startup. Ignored on linux.", default=False)
        parser.add_option('--root', action="store_true", dest="allow_root", help="Allow CCM to start cassandra as root", default=False)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        try:
            self.node.start(not self.options.no_join_ring,
                            no_wait=self.options.no_wait,
                            wait_other_notice=self.options.wait_other_notice,
                            wait_for_binary_proto=self.options.wait_for_binary_proto,
                            verbose=self.options.verbose,
                            replace_address=self.options.replace_address,
                            jvm_args=self.options.jvm_args,
                            quiet_start=self.options.quiet_start,
                            allow_root=self.options.allow_root)
        except NodeError as e:
            print_(str(e), file=sys.stderr)
            print_("Standard error output is:", file=sys.stderr)
            for line in e.process.stderr:
                print_(line.rstrip('\n'), file=sys.stderr)
            exit(1)


class NodeStopCmd(Cmd):

    def description(self):
        return "Stop a node"

    def get_parser(self):
        usage = "usage: ccm node stop [options] name"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('--no-wait', action="store_true", dest="no_wait",
                          help="Do not wait for the node to be stopped", default=False)
        parser.add_option('-g', '--gently', action="store_const", dest="signal_event",
                          help="Shut down gently (default)", const=signal.SIGTERM,
                          default=signal.SIGTERM)

        if common.is_win():
            # Fill the dictionary with SIGTERM as the cluster is killed forcefully
            # on Windows regardless of assigned signal (TASKKILL is used)
            default_signal_events = { '1': signal.SIGTERM, '9': signal.SIGTERM }
        else:
            default_signal_events = { '1': signal.SIGHUP, '9': signal.SIGKILL }

        parser.add_option('--hang-up', action="store_const", dest="signal_event",
                          help="Shut down via hang up (kill -1)",
                          const=default_signal_events['1'])
        parser.add_option('--not-gently', action="store_const", dest="signal_event",
                          help="Shut down immediately (kill -9)",
                          const=default_signal_events['9'])
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        try:
            if not self.node.stop(wait=not self.options.no_wait, signal_event=self.options.signal_event):
                print_("%s is not running" % self.name, file=sys.stderr)
                exit(1)
        except NodeError as e:
            print_(str(e), file=sys.stderr)
            exit(1)


class _NodeToolCmd(Cmd):
    usage = "This is a private class, how did you get here?"
    descr_text = "This is a private class, how did you get here?"
    nodetool_cmd = ''

    def get_parser(self):
        parser = self._get_default_parser(self.usage, self.description())
        return parser

    def description(self):
        return self.descr_text

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        stdout, stderr, rc = self.node.nodetool(self.nodetool_cmd + " " + " ".join((self.args[1:])))
        print_(stderr)
        print_(stdout)


class NodeNodetoolCmd(_NodeToolCmd):
    usage = "usage: ccm node_name nodetool [options]"
    descr_text = "Run nodetool (connecting to node name)"

    def run(self):
        stdout, stderr, rc = self.node.nodetool(" ".join(self.args[1:]))
        print_(stderr)
        print_(stdout)


class NodeRingCmd(_NodeToolCmd):
    usage = "usage: ccm node_name ring [options]"
    nodetool_cmd = 'ring'
    descr_text = "Print ring (connecting to node name)"


class NodeStatusCmd(_NodeToolCmd):
    usage = "usage: ccm node_name status [options]"
    nodetool_cmd = 'status'
    descr_text = "Print status (connecting to node name)"


class NodeFlushCmd(_NodeToolCmd):
    usage = "usage: ccm node_name flush [options]"
    nodetool_cmd = 'flush'
    descr_text = "Flush node name"


class NodeCompactCmd(_NodeToolCmd):
    usage = "usage: ccm node_name compact [options]"
    nodetool_cmd = 'compact'
    descr_text = "Compact node name"


class NodeDrainCmd(_NodeToolCmd):
    usage = "usage: ccm node_name drain [options]"
    nodetool_cmd = 'drain'
    descr_text = "Drain node name"


class NodeCleanupCmd(_NodeToolCmd):
    usage = "usage: ccm node_name cleanup [options]"
    nodetool_cmd = 'cleanup'
    descr_text = "Run cleanup on node name"


class NodeRepairCmd(_NodeToolCmd):
    usage = "usage: ccm node_name repair [options]"
    nodetool_cmd = 'repair'
    descr_text = "Run repair on node name"


class NodeVersionCmd(_NodeToolCmd):
    usage = "usage: ccm node_name version"
    nodetool_cmd = 'version'
    descr_text = "Get the cassandra version of node"


class NodeDecommissionCmd(_NodeToolCmd):
    usage = "usage: ccm node_name decommission [options]"
    nodetool_cmd = 'decommission'
    descr_text = "Run decommission on node name"

    def get_parser(self):
        parser = self._get_default_parser(self.usage, self.description())
        parser.add_option('--force', action="store_true", dest="force",
                help="Force decommission of this node even when it reduces the number of replicas to below configured RF.  Note: This is only relevant for C* 3.12+.", default=False)
        return parser

    def run(self):
        self.node.decommission(force=self.options.force)


class _DseToolCmd(Cmd):
    usage = "This is a private class, how did you get here?"
    descr_text = "This is a private class, how did you get here?"
    dsetool_cmd = ''

    def get_parser(self):
        parser = self._get_default_parser(self.usage, self.description())
        return parser

    def description(self):
        return self.descr_text

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        self.node.dsetool(self.dsetool_cmd)


class NodeDsetoolCmd(_DseToolCmd):
    usage = "usage: ccm node_name dsetool [options]"
    descr_text = "Run dsetool (connecting to node name)"

    def run(self):
        self.node.dsetool(" ".join(self.args[1:]))


class NodeCliCmd(Cmd):

    def description(self):
        return "Launch a cassandra cli connected to this node"

    def get_parser(self):
        usage = "usage: ccm node_name cli [options] [cli_options]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        parser.add_option('-x', '--exec', type="string", dest="cmds", default=None,
                          help="Execute the specified commands and exit")
        parser.add_option('-v', '--verbose', action="store_true", dest="verbose",
                          help="With --exec, show cli output after completion", default=False)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.cli_options = parser.get_ignored() + args[1:]

    def run(self):
        out, err, rc = self.node.run_cli(self.options.cmds, self.cli_options)
        if self.options.verbose:
            print_("CLI OUTPUT:\n-------------------------------")
            print_(out)
            print_("-------------------------------\nCLI ERROR:\n-------------------------------")
            print_(err)


class NodeCqlshCmd(Cmd):

    def description(self):
        return "Launch a cqlsh session connected to this node"

    def get_parser(self):
        usage = "usage: ccm node_name cqlsh [options] [cli_options]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        parser.add_option('-x', '--exec', type="string", dest="cmds", default=None,
                          help="Execute the specified commands and exit")
        parser.add_option('-v', '--verbose', action="store_true", dest="verbose",
                          help="With --exec, show cli output after completion", default=False)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.cqlsh_options = parser.get_ignored() + args[1:]

    def run(self):
        self.node.run_cqlsh(self.options.cmds, self.cqlsh_options)


class NodeBulkloadCmd(Cmd):

    def description(self):
        return "Bulkload files into the cluster by connecting to this node"

    def get_parser(self):
        usage = "usage: ccm node_name bulkload [options] [sstable_dir]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.loader_options = parser.get_ignored() + args[1:]

    def run(self):
        self.node.bulkload(self.loader_options)


class NodeScrubCmd(Cmd):

    def description(self):
        return "Scrub files"

    def get_parser(self):
        usage = "usage: ccm node_name scrub [options] <keyspace> <cf>"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.scrub_options = parser.get_ignored() + args[1:]

    def run(self):
        self.node.scrub(self.scrub_options)


class NodeVerifyCmd(Cmd):

    def description(self):
        return "Verify files"

    def get_parser(self):
        usage = "usage: ccm node_name verify [options] <keyspace> <cf>"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.verify_options = parser.get_ignored() + args[1:]

    def run(self):
        self.node.verify(self.verify_options)


class NodeJsonCmd(Cmd):

    def description(self):
        return "Call sstable2json/sstabledump on the sstables of this node"

    def get_parser(self):
        usage = "usage: ccm node_name json [options] [file]"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('-k', '--keyspace', type="string", dest="keyspace", default=None,
                          help="The keyspace to use [use all keyspaces by default]")
        parser.add_option('-c', '--column-families', type="string", dest="cfs", default=None,
                          help="Comma separated list of column families to use (requires -k to be set)")
        parser.add_option('--key', type="string", action="append", dest="keys", default=None,
                          help="The key to include (you may specify multiple --key)")
        parser.add_option('-e', '--enumerate-keys', action="store_true", dest="enumerate_keys",
                          help="Only enumerate keys (i.e, call sstable2keys)", default=False)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.keyspace = options.keyspace
        if self.keyspace is None:
            print_("You must specify a keyspace.")
            parser.print_help()
            exit(1)
        self.outfile = args[-1] if len(args) >= 2 else None
        self.column_families = options.cfs.split(',') if options.cfs else None

    def run(self):
        try:
            f = sys.stdout
            if self.outfile is not None:
                f = open(self.outfile, 'w')
            if self.node.has_cmd('sstable2json'):
                self.node.run_sstable2json(keyspace=self.keyspace,
                                           out_file=f,
                                           column_families=self.column_families,
                                           keys=self.options.keys,
                                           enumerate_keys=self.options.enumerate_keys)
            elif self.node.has_cmd('sstabledump'):
                self.node.run_sstabledump(keyspace=self.keyspace,
                                          column_families=self.column_families,
                                          keys=self.options.keys,
                                          enumerate_keys=self.options.enumerate_keys,
                                          command=True)
        except common.ArgumentError as e:
            print_(e, file=sys.stderr)


class NodeSstablesplitCmd(Cmd):

    def description(self):
        return "Run sstablesplit on the sstables of this node"

    def get_parser(self):
        usage = "usage: ccm node_name sstablesplit [options] [file]"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('-k', '--keyspace', type="string", dest="keyspace", default=None,
                          help="The keyspace to use [use all keyspaces by default]")
        parser.add_option('-c', '--column-families', type="string", dest='cfs', default=None,
                          help="Comma separated list of column families to use (requires -k to be set)")
        parser.add_option('-s', '--size', type='int', dest="size", default=None,
                          help="Maximum size in MB for the output sstables (default: 50 MB)")
        parser.add_option('--no-snapshot', action='store_true', dest="no_snapshot", default=False,
                          help="Don't snapshot the sstables before splitting")
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.keyspace = options.keyspace
        self.size = options.size
        self.no_snapshot = options.no_snapshot
        self.column_families = None
        self.datafiles = None
        if options.cfs is not None:
            if self.keyspace is None:
                print_("You need a keyspace (option -k) if you specify column families", file=sys.stderr)
                exit(1)
            self.column_families = options.cfs.split(',')

        if len(args) > 1:
            if self.column_families is None:
                print_("You need a column family (option -c) if you specify datafiles", file=sys.stderr)
                exit(1)
            self.datafiles = args[1:]

    def run(self):
        self.node.run_sstablesplit(datafiles=self.datafiles, keyspace=self.keyspace,
                                   column_families=self.column_families, size=self.size,
                                   no_snapshot=self.no_snapshot)


class NodeGetsstablesCmd(Cmd):

    def description(self):
        return "Run getsstables to get absolute path of sstables in this node"

    def get_parser(self):
        usage = "usage: ccm node_name getsstables [options] [file]"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('-k', '--keyspace', type="string", dest="keyspace", default=None,
                          help="The keyspace to use [use all keyspaces by default]")
        parser.add_option('-t', '--tables', type="string", dest='tables', default=None,
                          help="Comma separated list of tables to use (requires -k to be set)")
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.keyspace = options.keyspace
        self.tables = None
        self.datafiles = None
        if options.tables is not None:
            if self.keyspace is None:
                print_("You need a keyspace (option -k) if you specify tables", file=sys.stderr)
                exit(1)
            self.tables = options.tables.split(',')

        if len(args) > 1:
            if self.tables is None:
                print_("You need a tables (option -t) if you specify datafiles", file=sys.stderr)
                exit(1)
            self.datafiles = args[1:]

    def run(self):
        sstablefiles = self.node.get_sstablespath(datafiles=self.datafiles, keyspace=self.keyspace,
                                                  tables=self.tables)
        print_('\n'.join(sstablefiles))


class NodeUpdateconfCmd(Cmd):

    def description(self):
        return "Update the cassandra config files for this node (useful when updating cassandra)"

    def get_parser(self):
        usage = "usage: ccm node_name updateconf [options] [ new_setting | ...  ], where new_setting should be a string of the form 'compaction_throughput_mb_per_sec: 32'"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('--no-hh', '--no-hinted-handoff', action="store_false",
                          dest="hinted_handoff", default=True, help="Disable hinted handoff")
        parser.add_option('--batch-cl', '--batch-commit-log', action="store_true",
                          dest="cl_batch", default=None, help="Set commit log to batch mode")
        parser.add_option('--periodic-cl', '--periodic-commit-log', action="store_true",
                          dest="cl_periodic", default=None, help="Set commit log to periodic mode")
        parser.add_option('--rt', '--rpc-timeout', action="store", type='int',
                          dest="rpc_timeout", help="Set rpc timeout")
        parser.add_option('-y', '--yaml', action="store_true", dest="literal_yaml",
                          default=False, help="Pass in literal yaml string. Option syntax looks like ccm node_name updateconf -y 'a: [b: [c,d]]'")
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        args = args[1:]
        try:
            self.setting = common.parse_settings(args, literal_yaml=self.options.literal_yaml)
            if self.options.cl_batch and self.options.cl_periodic:
                print_("Can't set commitlog to be both batch and periodic.{}".format(os.linesep))
                parser.print_help()
                exit(1)
        except common.ArgumentError as e:
            print_(str(e), file=sys.stderr)
            exit(1)

    def run(self):
        self.setting['hinted_handoff_enabled'] = self.options.hinted_handoff
        if self.options.rpc_timeout is not None:
            if self.node.cluster.cassandra_version() < "1.2":
                self.setting['rpc_timeout_in_ms'] = self.options.rpc_timeout
            else:
                self.setting['read_request_timeout_in_ms'] = self.options.rpc_timeout
                self.setting['range_request_timeout_in_ms'] = self.options.rpc_timeout
                self.setting['write_request_timeout_in_ms'] = self.options.rpc_timeout
                self.setting['truncate_request_timeout_in_ms'] = self.options.rpc_timeout
                self.setting['request_timeout_in_ms'] = self.options.rpc_timeout
        self.node.set_configuration_options(values=self.setting)
        if self.options.cl_batch:
            self.node.set_batch_commitlog(True)
        if self.options.cl_periodic:
            self.node.set_batch_commitlog(False)


class NodeUpdatedseconfCmd(Cmd):

    def description(self):
        return "Update the dse config files for this node"

    def get_parser(self):
        usage = "usage: ccm node_name updatedseconf [options] [ new_setting | ...  ], where new setting should be a string of the form 'max_solr_concurrency_per_core: 2'; nested options can be separated with a period like 'cql_slow_log_options.enabled: true'"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('-y', '--yaml', action="store_true", dest="literal_yaml", default=False, help="Pass in literal yaml string. Option syntax looks like ccm node_name updatedseconf -y 'a: [b: [c,d]]'")
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        args = args[1:]
        try:
            self.setting = common.parse_settings(args, literal_yaml=self.options.literal_yaml)
        except common.ArgumentError as e:
            print_(str(e), file=sys.stderr)
            exit(1)

    def run(self):
        self.node.set_dse_configuration_options(values=self.setting)

#
# Class implementens the functionality of updating log4j-server.properties
# on the given node by copying the given config into
# ~/.ccm/name-of-cluster/nodeX/conf/log4j-server.properties
#


class NodeUpdatelog4jCmd(Cmd):

    def description(self):
        return "Update the Cassandra log4j-server.properties configuration file under given node"

    def get_parser(self):
        usage = "usage: ccm node_name updatelog4j -p <log4j config>"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('-p', '--path', type="string", dest="log4jpath",
                          help="Path to new Cassandra log4j configuration file")
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        try:
            self.log4jpath = options.log4jpath
            if self.log4jpath is None:
                raise KeyError("[Errno] -p or --path <path of new log4j configuration file> is not provided")
        except common.ArgumentError as e:
            print_(str(e), file=sys.stderr)
            exit(1)
        except KeyError as e:
            print_(str(e), file=sys.stderr)
            exit(1)

    def run(self):
        try:
            self.node.update_log4j(self.log4jpath)
        except common.ArgumentError as e:
            print_(str(e), file=sys.stderr)
            exit(1)


class NodeStressCmd(Cmd):

    def description(self):
        return "Run stress on a node"

    def get_parser(self):
        usage = "usage: ccm node_name stress [options] [stress_options]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.stress_options = args[1:] + parser.get_ignored()

    def run(self):
        try:
            self.node.stress(self.stress_options)
        except OSError:
            print_("Could not find stress binary (you may need to build it)", file=sys.stderr)


class NodeShuffleCmd(Cmd):

    def description(self):
        return "Run shuffle on a node"

    def get_parser(self):
        usage = "usage: ccm node_name shuffle [options] [shuffle_cmds]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.shuffle_cmd = args[1]

    def run(self):
        self.node.shuffle(self.shuffle_cmd)


class NodeSetdirCmd(Cmd):

    def description(self):
        return "Set the cassandra directory to use for the node"

    def get_parser(self):
        usage = "usage: ccm node_name setdir [options]"
        parser = self._get_default_parser(usage, self.description())
        parser.add_option('-v', "--version", type="string", dest="version",
                          help="Download and use provided cassandra or dse version. If version is of the form 'git:<branch name>', then the specified branch will be downloaded from the git repo and compiled. (takes precedence over --install-dir)", default=None)
        parser.add_option("--install-dir", type="string", dest="install_dir",
                          help="Path to the cassandra or dse directory to use [default %default]", default="./")
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        try:
            self.node.set_install_dir(install_dir=self.options.install_dir, version=self.options.version, verbose=True)
        except common.ArgumentError as e:
            print_(str(e), file=sys.stderr)
            exit(1)


class NodeSetworkloadCmd(Cmd):

    def description(self):
        return "Sets the workloads for a DSE node"

    def get_parser(self):
        usage = "usage: ccm node_name setworkload [cassandra|solr|hadoop|spark|dsefs|cfs|graph],..."
        parser = self._get_default_parser(usage, self.description())
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.workloads = args[1].split(',')
        valid_workloads = ['cassandra', 'solr', 'hadoop', 'spark', 'dsefs', 'cfs', 'graph']
        for workload in self.workloads:
            if workload not in valid_workloads:
                print_(workload, ' is not a valid workload')
                exit(1)

    def run(self):
        try:
            self.node.set_workloads(workloads=self.workloads)
        except common.ArgumentError as e:
            print_(str(e), file=sys.stderr)
            exit(1)


class NodeDseCmd(Cmd):

    def description(self):
        return "Launch a dse client application connected to this node"

    def get_parser(self):
        usage = "usage: ccm node_name dse [dse_options]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.dse_options = args[1:] + parser.get_ignored()

    def run(self):
        self.node.dse(self.dse_options)


class NodeHadoopCmd(Cmd):

    def description(self):
        return "Launch a hadoop session connected to this node"

    def get_parser(self):
        usage = "usage: ccm node_name hadoop [options] [hadoop_options]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.hadoop_options = args[1:] + parser.get_ignored()

    def run(self):
        self.node.hadoop(self.hadoop_options)


class NodeHiveCmd(Cmd):

    def description(self):
        return "Launch a hive session connected to this node"

    def get_parser(self):
        usage = "usage: ccm node_name hive [options] [hive_options]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.hive_options = args[1:] + parser.get_ignored()

    def run(self):
        self.node.hive(self.hive_options)


class NodePigCmd(Cmd):

    def description(self):
        return "Launch a pig session connected to this node"

    def get_parser(self):
        usage = "usage: ccm node_name pig [options] [pig_options]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.pig_options = parser.get_ignored() + args[1:]

    def run(self):
        self.node.pig(self.pig_options)


class NodeSqoopCmd(Cmd):

    def description(self):
        return "Launch a sqoop session connected to this node"

    def get_parser(self):
        usage = "usage: ccm node_name sqoop [options] [sqoop_options]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.sqoop_options = args[1:] + parser.get_ignored()

    def run(self):
        self.node.sqoop(self.sqoop_options)


class NodeSparkCmd(Cmd):

    def description(self):
        return "Launch a spark session connected to this node"

    def get_parser(self):
        usage = "usage: ccm node_name spark [options] [spark_options]"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.spark_options = args[1:] + parser.get_ignored()

    def run(self):
        self.node.spark(self.spark_options)


class NodePauseCmd(Cmd):

    def description(self):
        return "Send a SIGSTOP to this node"

    def get_parser(self):
        usage = "usage: ccm node_name pause"
        parser = self._get_default_parser(usage, self.description())
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        self.node.pause()


class NodeResumeCmd(Cmd):

    def description(self):
        return "Send a SIGCONT to this node"

    def get_parser(self):
        usage = "usage: ccm node_name resume"
        parser = self._get_default_parser(usage, self.description())
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        self.node.resume()


class NodeJconsoleCmd(Cmd):

    def description(self):
        return "Opens jconsole client and connect to running node"

    def get_parser(self):
        usage = "usage: ccm node_name jconsole"
        return self._get_default_parser(usage, self.description())

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        cmds = ["jconsole", "localhost:%s" % self.node.jmx_port]
        try:
            subprocess.call(cmds)
        except OSError:
            print_("Could not start jconsole. Please make sure jconsole can be found in your $PATH.")
            exit(1)


class NodeVersionfrombuildCmd(Cmd):

    def description(self):
        return "Print the node's version as grepped from build.xml. Can be used when the node isn't running."

    def get_parser(self):
        usage = "usage: ccm node_name versionfrombuild"
        parser = self._get_default_parser(usage, self.description())
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)

    def run(self):
        print_(common.get_version_from_build(self.node.get_install_dir()))


class NodeBytemanCmd(Cmd):

    def description(self):
        return "Invoke byteman-submit "

    def get_parser(self):
        usage = "usage: ccm node_name byteman-submit"
        parser = self._get_default_parser(usage, self.description(), ignore_unknown_options=True)
        return parser

    def validate(self, parser, options, args):
        Cmd.validate(self, parser, options, args, node_name=True, load_cluster=True)
        self.byteman_options = args[1:] + parser.get_ignored()

    def run(self):
        self.node.byteman_submit(self.byteman_options)
