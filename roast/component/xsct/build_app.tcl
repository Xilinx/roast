set option {
    {xsa.arg               ""                  "XSA file"}
    {processor.arg         ""                  "target processor"}
    {osname.arg            "standalone"        "target OS"}
    {rp.arg                ""                  "repo path"}
    {app.arg               "Empty Application" "Application project fsbl, empty.."}
    {pname.arg             ""                  "Project Name"}
    {ws.arg                ""                  "Work Space Path"}
}

set usage  "xsct app.tcl <arguments>"
array set params [cmdline::getoptions argv $option $usage]

setws $params(ws)
repo -set $params(rp)

#Create Application
app create -name $params(pname) -template \
    $params(app) -proc $params(processor) \
        -os $params(osname) -hw $params(xsa)

platform generate
#Build Application
app build -name $params(pname)
