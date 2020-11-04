setws ./plm
repo -set $env(ESWREPO_PATH)
app create -name plm -template {versal PLM} -proc psv_pmc_0 -os standalone -hw ../design_1_wrapper.xsa
app build -name plm
