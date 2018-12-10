from subprocess import Popen, PIPE
import sys
import yaml


class RestoreTable:
    def __init__(self,
                 storage_dir='/tmp/',
                 master_conf='autodump_master.yml',
                 slave_conf='autodump.yml',
                 my_cnf=None,
                 my_cnf_suffix_dump='mysqldumpDump',
                 my_cnf_suffix_restore='mysqldumpRestore'):

        self.storage_dir = storage_dir
        self.m_conf = master_conf
        self.s_conf = slave_conf
        self.my_cnf = my_cnf
        self.my_cnf_suffix_dump = my_cnf_suffix_dump
        self.my_cnf_suffix_restore = my_cnf_suffix_restore

    # Create dump file
    def mysqldump_dump(self, host, port, database, table, user=False, password=False, where=False):

        cmd = '/usr/bin/mysqldump'
        cmd_opt = ' --innodb-optimize-keys' \
                  ' --single-transaction' \
                  ' --extended-insert' \
                  ' --max-allowed-packet=250M' \
                  ' --skip-triggers'

        if self.my_cnf:
            cmd_line = '{cmd} --defaults-extra-file={my_cnf} --defaults-group-suffix={my_cnf_suffix_dump}' \
                       ' {opt} {db} {tbl} '.format(cmd=cmd,
                                                   my_cnf=self.my_cnf,
                                                   my_cnf_suffix_dump=self.my_cnf_suffix_dump,
                                                   opt=cmd_opt,
                                                   port=port,
                                                   db=database,
                                                   tbl=table)
        elif user and password:
            cmd_line = '{cmd} {opt} -h {host} -P {port}' \
                       ' -u {user} -p{pas} {db} {tbl} '.format(cmd=cmd,
                                                               opt=cmd_opt,
                                                               host=host,
                                                               port=port,
                                                               user=user,
                                                               pas=password,
                                                               db=database,
                                                               tbl=table)
        else:
            print('No required argument was given: '
                  ' `my_cnf` file or `user` and `password` args in `master_conf` file')
            sys.exit(1)

        if where:
            return cmd_line.split() + ['--where=\'{}\''.format(where)]
        else:
            return cmd_line.split()

    # Restore from dump_file
    def mysqldump_restore(self, host, port, database, user=False, password=False):
        cmd = 'mysql'
        if self.my_cnf:
            cmd_line = '{cmd} --defaults-extra-file={my_cnf} --defaults-group-suffix={my_cnf_suffix_restore}' \
                       ' {db} '.format(cmd=cmd,
                                       my_cnf=self.my_cnf,
                                       my_cnf_suffix_restore=self.my_cnf_suffix_restore,
                                       db=database)
        elif user and password:
            cmd_line = '{cmd} -h {host} -P {port}' \
                       ' -u {user} -p{pas} {db} '.format(cmd=cmd,
                                                         host=host,
                                                         port=port,
                                                         user=user,
                                                         pas=password,
                                                         db=database
                                                         )
        else:
            print('No required argument was given: '
                  ' `my_cnf` file or `user` and `password` args in `master_conf` file')
            sys.exit(1)

        return cmd_line.split()

    # Execute dump command
    def dump_executor(self, command, dst_file):
        print(command)
        with open(dst_file, 'w') as out_file:
            pipe = Popen(command, universal_newlines=True, stdin=PIPE, stderr=PIPE, stdout=out_file)
            stdout, stderr = pipe.communicate()
            if pipe.returncode != 0:
                print('Error: mysqldump did not create the dst_file ' + dst_file)
                print(stderr)
                return False
            else:
                print('Success: mysqldump backup create the dst_file ' + dst_file)
                return True

    # Execute restore from dump
    def dump_apply(self, command, src_file):
        print(command)
        with open(src_file, 'r') as in_file:
            pipe = Popen(command, universal_newlines=True, stderr=PIPE, stdin=in_file)
            stdout, stderr = pipe.communicate()
            if pipe.returncode != 0:
                print('Error: mysqldump did not restore the src_file ' + src_file)
                print(stderr)
                return False
            else:
                print('Success: mysqldump restore the the src_file ' + src_file)
                return True

    # Main method for executing all of methods above
    def my_backup(self):
        with open(self.m_conf, 'r', encoding='utf8') as m_conf_file:
            m_info = yaml.load(m_conf_file)

        m_connect = {
            'user':     m_info['restore']['master']['user'],
            'password': m_info['restore']['master']['password'],
            'host':     m_info['restore']['master']['host'],
            'port':     m_info['restore']['master']['port'],
        }

        with open(self.s_conf, 'r', encoding='utf8') as s_conf_file:
            s_info = yaml.load(s_conf_file)

        s_connect = {
            'user':       s_info['restore']['slave']['user'],
            'password':   s_info['restore']['slave']['password'],
            'host':       s_info['restore']['slave']['host'],
            'port':       s_info['restore']['slave']['port'],
        }

        for s_db, s_dbs_info in s_info['restore']['slave']['databases'].items():
            for table, add_opt in s_dbs_info.items():
                print('DB: ', s_db)
                print('TBL: ', table)
                print('WHERE: ', add_opt['where'])
                cmd_dump = self.mysqldump_dump(host=m_connect['host'],
                                               port=m_connect['port'],
                                               database=s_db,
                                               table=table,
                                               user=m_connect['user'],
                                               password=m_connect['password'],
                                               where=add_opt['where']
                                               )
                execute_dump = self.dump_executor(cmd_dump, self.storage_dir + table + '.sql')

                if execute_dump:
                    print("SUCCESS!")

                    if add_opt['restore_to_db']:
                        cmd_restore = self.mysqldump_restore(host=s_connect['host'],
                                                             port=s_connect['port'],
                                                             database=add_opt['restore_to_db'],
                                                             user=s_connect['user'],
                                                             password=s_connect['password'],
                                                             )
                    else:
                        cmd_restore = self.mysqldump_restore(host=s_connect['host'],
                                                             port=s_connect['port'],
                                                             database=s_db,
                                                             user=s_connect['user'],
                                                             password=s_connect['password'],
                                                             )

                    self.dump_apply(cmd_restore, self.storage_dir + table + '.sql')

                else:
                    print("DUMP WAS FAILED!")

        return True


dumper_instance = RestoreTable(my_cnf='.my.cnf', my_cnf_suffix_dump='mysqldumpDump')
dumper_instance.my_backup()
