import argparse

workerSubFile = 'worker.sub'
workerDockerImage = 'nathanlazarus/direscuworker:v0'

masterSubFile = 'master.sub'
masterDockerImage = 'nathanlazarus/direscumaster:v0'

parameterFile = 'InitPara_det.txt'
deterministicSolFile = 'params_Social_IES1.5.put'
additionalDataFile = 'SpatialPopAnn.csv'

WhichStage = 'WhichStage.txt'

ncores_init = 4
ncores_master_non_init = 1


parser = argparse.ArgumentParser()
parser.add_argument('Nworkers', type = int, help = 'number of worker machines')
parser.add_argument('NumTaskCont', type = int, help = 'number of continuous tasks per discrete state')
parser.add_argument('-init', '-initialize', type = int, help = 'initialize to do INIT + 1 iterations')
args = parser.parse_args()

if args.init != None:
	thisStage = 'init'
	workerfiles = ''
	ncores_master = ncores_init
	with open(WhichStage, 'w') as f:
		f.write(str(args.init))
else:
	with open(WhichStage, 'r') as f:
		thisStage = int(next(f))

	nextStage = thisStage - 1

	with open(WhichStage, 'w') as f:
		f.write(str(nextStage))

	ncores_master = ncores_master_non_init


	worker_sub_text = """\
# {0}

workerID                = $(Process) + 1
universe                = docker
docker_image            = {1}
executable              = /code/ClimateWorker
transfer_executable     = False
arguments               = 3 {2} {3} {4} -p {5} --nworkers {6} -i $INT(workerID)
transfer_input_files    = {2}, {5}, {7}, ValFunCoefs{8}.nc
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
error                   = outfiles/worker{4}_$INT(workerID).err
output                  = outfiles/worker{4}_$INT(workerID).out
log                     = outfiles/worker{4}.log
max_retries             = 10
periodic_release        = (HoldReasonCode == 35) && (NumJobStarts < 10)

Rank                    = kflops
request_disk            = 18GB
request_memory          = 40GB
queue {6}
""".format(workerSubFile, workerDockerImage, parameterFile, args.NumTaskCont, thisStage, deterministicSolFile, args.Nworkers, additionalDataFile, thisStage + 1)


	with open(workerSubFile, 'w') as sub_file:
	    sub_file.write(worker_sub_text)

	workerfiles = ', ' + ', '.join(['buffer' + str(thisStage) + '_' + str(x) + '.nc' for x in range(1, args.Nworkers + 1)])






master_sub_text = """\
# {0}

universe                = docker
docker_image            = {1}
executable              = mpiexec
transfer_executable     = False
arguments               = -n {9} --allow-run-as-root /code/ClimateMaster 2 {2} {3} {4} -p {5} --nworkers {6}
transfer_input_files    = {2}, {5}, {7}{8}
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
error                   = outfiles/master{4}.err
output                  = outfiles/master{4}.out
log                     = outfiles/master{4}.log
request_cpus            = {9}
max_retries             = 10
periodic_release        = (HoldReasonCode == 35) && (NumJobStarts < 10)

Rank                    = kflops
request_disk            = 18GB
request_memory          = 40GB
queue
""".format(masterSubFile, masterDockerImage, parameterFile, args.NumTaskCont, thisStage, deterministicSolFile, args.Nworkers, additionalDataFile, workerfiles, ncores_master)

with open(masterSubFile, 'w') as sub_file:
    sub_file.write(master_sub_text)
