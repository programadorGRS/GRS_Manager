#!/bin/bash

# source: https://www.folio3.com/5-easy-steps-on-scheduling-mysql-database-backup-using-cron

# (1) set up all the mysqldump variables
DATE=`date +"%d_%m_%Y_%H%M"`
SQLFILE=/home/ubuntu/backups/manager_db2_backup_${DATE}.sql
DATABASE=manager_db2
USER=
PASSWORD=

# (2) in case you run this more than once a day,
# remove the previous version of the file
#unalias rm     2> /dev/null
#rm ${SQLFILE}     2> /dev/null
#rm ${SQLFILE}.gz  2> /dev/null

# (3) do the mysql database backup (dump)
sudo mysqldump -u ${USER} -p${PASSWORD} ${DATABASE}|gzip > ${SQLFILE}.gz

# limpar arquivos antigos (mais antigos q 7 dias)
find backups/ -mtime +7 -exec rm {} \;

