#!/usr/bin/python

import re,argparse,datetime,os
from jenkinsapi.jenkins import Jenkins
from argparse import RawTextHelpFormatter


WORK_DIR = os.getcwd() + '/'
JOB_CONF_TEMPLATE = WORK_DIR + 'etc/templates/template.xml.conf'
PROJECTS_CONF_FILE = WORK_DIR + 'etc/projects.dict.conf'
BUILDPARAMS_CONF_FILE = WORK_DIR + 'etc/buildparams.conf'
SELF_CONF_FILE = WORK_DIR + 'etc/mjcreator.conf'

def get_time(mode):
    now = datetime.datetime.now()

    if mode == 'machine':
        return '%s%s%s_%s%s%s' % (now.hour, now.minute, now.second, now.day, now.month, now.year)
    elif mode == 'human':
        return '%s:%s:%s %s.%s.%s' % (now.hour, now.minute, now.second, now.day, now.month, now.year)
    else:
        return 'set valid mode for get_time()'

CREATE_JOBS_LOG = WORK_DIR + 'log/create_jobs_' + get_time('machine') + '.log'
CHECK_JOBS_LOG = WORK_DIR + 'log/check_jobs_' + get_time('machine') + '.log'
UPDATE_JOBS_LOG = WORK_DIR + 'log/update_jobs_' + get_time('machine') + '.log'

def create_arg_parser():
    parser = argparse.ArgumentParser(description='MJcreator: MultiJob Jenkins Creator' +
    '\nmain config for mjcreator: ' + SELF_CONF_FILE +
    '\nconfig list for projects: ' + PROJECTS_CONF_FILE +
    '\nxml template for jobs: ' + JOB_CONF_TEMPLATE +
    '\nbuild params for jobs: ' + BUILDPARAMS_CONF_FILE
    , formatter_class=RawTextHelpFormatter)
    parser.add_argument('--check', help='just checking statuses of latest builds contained in config', action = 'store_true')
    parser.add_argument('--create', help='create jobs contained in config', action = 'store_true')
    parser.add_argument('--project','-p',  help='create jobs from commandline.\n\n EXAMPLE: "./mjcreator.py --create -p testessay-site.com:223"')
    parser.add_argument('--update','-u',  help='update all vu-jobs from a template.', action = 'store_true')
    return parser

def get_server_instance():
    server = Jenkins(SelfConfDict['JENKINS_URL'], username = SelfConfDict['JENKINS_USERNAME'], password = SelfConfDict['JENKINS_PASSWORD'])
    return server

def parse_xmljob_conf():
    x = open(JOB_CONF_TEMPLATE, "r+")
    job_xml = x.read()
    x.close()
    return job_xml

def parse_projects_conf(typeparams):
    if typeparams == 'projects':
        c = open(PROJECTS_CONF_FILE, "r+")
    elif typeparams == 'buildparams':
        c = open(BUILDPARAMS_CONF_FILE, "r+")
    elif typeparams == 'selfconf':
        c = open(SELF_CONF_FILE, "r+")
    else:
        return 'Not set typeparams'

    ConfDict = {}

    for line in c:
        formated_line = line.strip('\n').split(':')
        if line.strip():
            key = formated_line[0]
            value = formated_line[1]
            ConfDict[key] = value
        else:
            pass

    c.close()
    return ConfDict

def parse_self_conf():
    SelfConfDict = {}
    c = open(SELF_CONF_FILE, "r+")

    for line in c:
        if line.strip():
            formated_line = line.strip('\n').replace(' ', '').split('=')
            key = formated_line[0]
            value = formated_line[1]
            SelfConfDict[key] = value
        else:
            pass

    c.close()
    return SelfConfDict

def create_jobs():
    J = get_server_instance()

    for key in ProjectsConfDict:
        ProjectName = key
        VuId = ProjectsConfDict[key]
        DstHost = 'vu-host' + VuId + '.mcemcw.com'
        DbName = ProjectName.replace('.', '_') + '_prod_db'
        GIT_SERVER = SelfConfDict['GIT_SERVER']

        JobSettings = {
        '%ProjectName%' : ProjectName,
        '%DbName%' : DbName,
        '%DstHost%' : DstHost,
        '%GitServer%' : GIT_SERVER
        }
        JobName = 'prod-vu' + VuId + '.seo-sites.' + ProjectName.replace('.', '-')

        job_xml = parse_xmljob_conf()

        for key in JobSettings:
            job_xml = job_xml.replace(key, JobSettings[key])

        NewJob = J.create_job(JobName, job_xml)
        print (get_time('human') + ' ' + JobName + ' - created')
        log.write((get_time('human') + ' ' + JobName + ' - created\n'))
        NewBuild = J.build_job(JobName, BuildParams)
        log.write((get_time('human') + ' ' + JobName + ' - builded\n'))
        print (get_time('human') + ' ' + JobName + ' - builded')
    return None

def check_build_status():
    Jobs = []

    for key in ProjectsConfDict:
        ProjectName = key
        VuId = ProjectsConfDict[key]
        JobName = 'prod-' + 'vu' + VuId + '.seo-sites.' + ProjectName.replace('.', '-')
        Jobs.append(JobName)

    J = get_server_instance()

    for JobName in Jobs:
        Job = J.get_job(JobName)
        LastBuild = Job.get_last_build_or_none()

        if LastBuild != None:
            Status = LastBuild.get_status()
        else:
            Status = 'Not builded yet'

        print (get_time('human') + ' ' + JobName + ' : ' + Status)
        log.write((get_time('human') + ' ' + JobName + ' : ' + Status))
    return None

def get_jobs():
    VuJobs = []
    for job in J.keys():
        if re.search('prod-vu2', job):
            VuJobs.append(job)
    return VuJobs

def get_job_conf(mode):
    XmlConfig = J[job].get_config()
    JobSet = {}
    JobSet['DstHost'] = re.findall('<configName>([a-zA-Z0-9\-\.]+)', XmlConfig)[0]
    JobSet['GIT_SERVER'] = re.findall('<url>([a-zA-Z0-9\-\.\@\/\:]+)', XmlConfig)[0]
    JobSet['ProjectName'] = re.findall('HOST_NAME=([a-zA-Z0-9\.\-]+)', XmlConfig)[0]
    JobSet['DbName'] = re.findall('DB_NAME=([a-zA-Z0-9\_\-]+)', XmlConfig)[0]

    if mode == 'JobSet':
        return JobSet
    if mode == 'XmlConfig':
        return XmlConfig

def update_job_conf():
    job_xml = parse_xmljob_conf()

    JobSettings = {
    '%ProjectName%' : JobSet['ProjectName'],
    '%DbName%' : JobSet['DbName'],
    '%DstHost%' : JobSet['DstHost'],
    '%GitServer%' : JobSet['GIT_SERVER']
    }

    for key in JobSettings:
        job_xml = job_xml.replace(key, JobSettings[key])

    J[job].update_config(job_xml)

    return None

args = create_arg_parser().parse_args()
SelfConfDict = parse_self_conf()

if args.create:
    if args.project:
        print ('onetime mode')
        ProjectsConfDict ={}
        ProjectsConfDict[args.project.split(':')[0]] = args.project.split(':')[1]
    else:
        ProjectsConfDict = parse_projects_conf('projects')
    log = open(CREATE_JOBS_LOG, 'wt')
    BuildParams = parse_projects_conf('buildparams')
    create_jobs()
    log.close()
elif args.check:
    if args.project:
        print ('onetime mode')
        ProjectsConfDict ={}
        ProjectsConfDict[args.project.split(':')[0]] = args.project.split(':')[1]
    else:
        ProjectsConfDict = parse_projects_conf('projects')
    log = open(CHECK_JOBS_LOG, 'wt')
    check_build_status()
    log.close()
elif args.update:
    log = open(UPDATE_JOBS_LOG, 'wt')
    J = get_server_instance()
    VuJobs = get_jobs()
    for job in VuJobs:
        try:
            JobSet = get_job_conf('JobSet')
            update_job_conf()
            log.write((get_time('human') + ' ' + job + ' : ' + 'updated!\n'))
            print (get_time('human') + ' ' + job + ' : ' + 'updated!\n')
        except Exception as e:
            log.write((get_time('human') + ' ' + job + ' : ' + str(e) + '\n'))
            print ((get_time('human') + ' ' + job + ' : ' + str(e) + '\n'))
    log.close()
else:
    create_arg_parser().print_help()
