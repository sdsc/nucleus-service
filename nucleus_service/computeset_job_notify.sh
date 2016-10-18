#!/bin/sh

SELF=$(/bin/readlink -f $0)
SELF_BASENAME=$(/bin/basename $SELF)
SELF_DIRNAME=$(/usr/bin/dirname $SELF)
LOGFILE=/tmp/${SELF_BASENAME}.out

. /etc/profile.d/modules.sh > $LOGFILE 2>&1
. /etc/profile.d/opt-modulefiles.sh >> $LOGFILE 2>&1

module load python >> $LOGFILE 2>&1
echo "Python environment" >> $LOGFILE 2>&1
module list >> $LOGFILE 2>&1
/usr/bin/which python >> $LOGFILE 2>&1
python --version >> $LOGFILE 2>&1

if [[ -f ${SELF_DIRNAME}/computeset_job_notify.py ]]; then
    cd ${SELF_DIRNAME}
    echo "Running script from... $(pwd)" >> $LOGFILE 2>&1
    echo "SLURM Environment variables available in this shelll..." >> $LOGFILE 2>&1
    printenv | /bin/grep SLURM >> $LOGFILE 2>&1
    echo "Calling ${SELF_DIRNAME}/computeset_job_notify.py" >> $LOGFILE 2>&1
    python ${SELF_DIRNAME}/computeset_job_notify.py >> $LOGFILE 2>&1
else
    echo "${SELF_DIRNAME}/computeset_job_notify.py not found" >> $LOGFILE 2>&1
fi

/bin/chown $SLURM_JOB_USER $LOGFILE
