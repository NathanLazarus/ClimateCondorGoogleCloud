createimages: condor-master condor-compute condor-submit
	@echo "createimages - done"

condor-master condor-compute condor-submit:
	@if [ -z "$$(gcloud compute images list --quiet --filter='name~^$@' --format=text)" ]; then \
	   echo "" ;\
	   echo "- building $@" ;\
	   echo ""; \
	   gcloud compute  instances create  $@-template \
	     --zone=us-east1-b \
	     --machine-type=m1-ultramem-40 \
	     --image=debian-9-stretch-v20210122 \
	     --image-project=debian-cloud \
	     --boot-disk-size=20GB \
	     --metadata-from-file startup-script=startup-scripts/$@.sh ; \
	   sleep 300 ;\
	   gcloud compute instances stop --zone=us-east1-b $@-template ;\
	   gcloud compute images create $@  \
	     --source-disk $@-template   \
	     --source-disk-zone us-east1-b   \
	     --family htcondor-debian ;\
	   gcloud compute instances delete --quiet --zone=us-east1-b $@-template ;\
	else \
	   echo "$@ image already exists"; \
	fi


deleteimages:
	-gcloud compute images delete --quiet condor-master
	-gcloud compute images delete --quiet condor-compute
	-gcloud compute images delete --quiet condor-submit

htcondor/run_htcondor.sh:
	cp htcondor/run_montecarlo.sh.orig htcondor/run_montecarlo.sh
ifneq ($(bucketname),)
	sed -i 's/YOURBUCKETNAME/${bucketname}/g' htcondor/run_montecarlo.sh 
endif

createcluster:
	@echo "creating a condor cluster using deployment manager scripts"
	gcloud deployment-manager deployments create condor-cluster --config deploymentmanager/condor-cluster.yaml
	
destroycluster:
	@echo "destroying the condor cluster"
	gcloud deployment-manager deployments delete condor-cluster

ssh:
ifeq ($(bucketname),)
	@echo "set the bucketname in order to copy some of the data and model files to the submit host"
	@echo "  make sshtocluster bucketname=<some bucket name>"
	gcloud compute ssh condor-submit
else
	@echo "using ${bucketname}"
	@echo "before sshing to the submit host, let me copy some of the files there to make"
	@echo "it easier for you."
	@echo "  - copying the model"
	gcloud compute ssh condor-submit --command "gsutil cp gs://${bucketname}/model/* ."
	@echo "  - copying the datafiles"
	gcloud compute ssh condor-submit --command "gsutil cp gs://${bucketname}/data/* ./"
	@echo "  - copying the condor submit files templates"
	gcloud compute ssh condor-submit --command "gsutil cp gs://${bucketname}/htcondor/* ."
	@echo "now just sshing"
	gcloud compute ssh condor-submit
endif


clean:
	rm link.file