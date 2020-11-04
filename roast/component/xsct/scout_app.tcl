package require cmdline
package require yaml
puts "script dir is: $::env(scriptsDir)"
source "$::env(scriptsDir)/utils.tcl"
set returncode 1
set option {
	{hdf.arg               ""                  "hardware Definition file"}
	{processor.arg         ""                  "target processor"}
	{osname.arg            "standalone"        "target OS"}
	{rp.arg                ""                  "repo path"}
	{app.arg               "Empty Application" "Application project fsbl, empty.."}
	{driver.arg            ""                  "Driver Name to be build"}
	{library_name.arg      ""                  "Library Name to be build"}
	{example_name.arg      ""                  "Example name to be build"}
	{out_dir.arg           ""                  "Output directory where the elfs will get copied after creation"}
	{lib.arg               ""                  "Add library"}
	{pname.arg             ""                  "Project Name"}
	{bspname.arg           ""                  "standalone bsp name"}
	{build_till_bsp.arg    "0"                 "Build till bsp only"}
	{ws.arg                ""                  "Work Space Path"}
	{hwpname.arg           ""                  "hardware project name"}
	{arch.arg              "64"                "32/64 bit architecture"}
	{do_compile.arg        "1"                 "Build the project, Default is True"}
	{do_cleanup.arg        "1"                 "Cleanup the project after build, Default is True"}
	{forceconf.arg         "0"                 "Apply the yaml comfigs on existing project"}
	{yamlconf.arg          ""                  "Path to Config File"}
	{extension.arg         ""                  "Run time functions to perform"}
	{rp_intg.arg           ""                  "INTG Repo Path"}
	{src.arg               ""                  "List of all source files needed"}
	{elf_name.arg          ""                  "Custom Elf Name"}
	{functest_name.arg     ""                  "Functional test name for intg cases"}
	{skip_examples.arg     ""                  "Examples that are not to be built"}
}

# re/auto generation of bsp is FALSE by default.
set autogenbsp 0

# Set Global Parameters
set conf_dict ""
set elf_dir_name "Debug"
set elf_name ""

set usage  "xsct app.tcl <arguments>"
array set params [cmdline::getoptions argv $option $usage]
set libs [split $params(lib) { }]
set examples [split $params(example_name) {,}]
set skip_examples [split $params(skip_examples) {,}]

proc build {type name} {
	$type build -name $name
}

# Set output elf directory name Release/Debug
proc set_elf_dir_name {} {
	if { $::conf_dict ne "" } {
		set app_dict [ get_key_value $::conf_dict "app" ]
		set property [ get_key_value $app_dict "build-config" ]
		set dir_name [ get_key_value $property "set" ]
		if { "$app_dict" ne "" && "$property" ne "" && "$dir_name" ne "" \
			&& [string tolower $dir_name]  eq "release" } {
			set ::elf_dir_name "Release"
		}
	}
}

proc do_armcc_config {} {
	if {[info exists ::env(TOOLCHAIN)] && $::env(TOOLCHAIN) eq "armcc" \
		&& $::params(processor) eq "ps7_cortexa9_0"} {
			bsp config compiler armcc
			bsp config archiver armar
			bsp config extra_compiler_flags -g
			platform generate
		}
}

proc set_tool_chain {} {
	if {[info exists ::env(TOOLCHAIN)] && $::env(TOOLCHAIN) eq "armcc" \
		&& $::params(processor) eq "ps7_cortexa9_0"} {
		toolchain "ps7_cortexa9" ARMCC
	}
}

proc set_app_conf {action prop val} {
	if { [catch {app config -name $::params(pname) -$action $prop $val} result] } {
		puts "ERROR:[info level 0]: Cannot set Property \"$prop\" with $val \n$result"
	}
}

proc set_bsp_conf {action prop val} {
	if { [catch {bsp config -name $::params(pname) -$action $prop $val} result] } {
		puts "ERROR:[info level 0]: Cannot set Property \"$prop\" with $val \n$result"
	}
	platform generate
}

proc xsct_config {type conf} {
	foreach prop [dict keys $conf] {
		foreach action [dict keys [dict get $conf $prop]] {
			set_$type\_conf $action $prop [dict get $conf $prop $action]
		}
	}
}

# Set library in the bsp
proc xsct_set_libs {addlib} {
	if { $addlib ne "" } {
		foreach l $addlib {
			bsp setlib -name $l
		}
		if { [ is_proc set_lib_property] } {
			set_lib_property
		}
		platform generate
	}
}

proc do_config {conf_dict component} {
	if { [dict exists $conf_dict $component] } {
		if { [catch {xsct_config $component [dict get $conf_dict $component]} result] } {
			puts "XSCTHELPER INFO: No $component configuration \n\t $result"
		}
	}
}

proc copy_verify_clean { } {
	set new_elf_name [get_elf_name]
	set default_elf_dir_path "$::params(ws)/$::params(pname)/$::elf_dir_name"
	verify_elf "$new_elf_name" "$default_elf_dir_path" "$::params(pname).elf"
	cleanup
}

# It sources the extension file if defined
proc source_extension {} {
	if { $::params(extension) ne ""} {
		# Collect all the extension files seperated by space
		set extensions [split $::params(extension) { }]
		# Iterate over all the extensions
		foreach extension $extensions {
			if { [is_file $extension] } {
				source $extension
			} else {
				# Error: Invalid extension file path
				puts stderr "ERROR: INVALID EXTENSION FILE PATH"
				exit 1
			}
		}
	}
}

# It reads component[driver/library], And returns list of all unique components present
# inside system.mss file and ignores those components for which src is not present
proc compute_latest_ver { component } {
	set comp_list ""
	set esw_comp ""
	set sw_path "$::params(ws)/$::params(hwpname)/export/$::params(hwpname)/sw"
	set mss_file [open "$sw_path/$::params(hwpname)/$::params(bspname)/system.mss" "r"]
	# To get all the components
	set name_list [split [read $mss_file] "\n"]
	# Get all the unique versions
	if { $component eq "driver" } {
		set esw_comp "$::params(driver)"
		set str1 "DRIVER_NAME"
		set str2 "DRIVER_VER"
	} elseif { $component eq "library" } {
		set esw_comp "$::params(library_name)"
		set str1 "LIBRARY_NAME"
		set str2 "LIBRARY_VER"
	}

	foreach name $name_list {
		if { $::env(BUILD_SOURCE) eq "sdk" } {
			if {[regexp $str1 $name]} {
				lassign [split $name "="] left_val right_val
				set comp [string trim $right_val]
			}
			if {[regexp $str2 $name]} {
				lassign [split $name "="] left_val right_val
				set comp_ver "_v[string map {. _} [string trim $right_val]]"
				set comp_name "${comp}${comp_ver}"
				lappend comp_list $comp_name
			}
		} else {
			if {[regexp $str1 $name]} {
				lassign [split $name "="] left_val right_val
				set comp [string trim $right_val]
				lappend comp_list $comp

			}
		}
	}

	if { [lsearch $comp_list $esw_comp*] < 0 || $comp_list eq "" } {
		puts stderr "ERROR: $esw_comp is not enabled in design/bsp!. Provide a valid xsa/hdf for given component"
		exit 1
	}

	# Create a list of unique versions which are at their latest level
	set comp_unique_list {}
	set item_list [list "cpu_cortexr5*" "cpu_cortexa53*" "cpu_cortexa9*" "generic*" "coresightps_dcc*" "ddrps*" "ddrcpsu*"]

	# Remove known component for which src code is not there
	foreach comp $comp_list {
		if {! [contains_any $comp $item_list] } {
			if { [lsearch $comp_unique_list $comp] < 0 } {
				lappend comp_unique_list $comp
			}
		}
	}

	close $mss_file
	return $comp_unique_list
}

# It reads all the components available in comp_list list and tries to find the latest
# version for comp_name, Exits if not found
proc get_comp_name_ver { comp_name comp_list } {
	foreach comp $comp_list {
		if { [string match ${comp_name}* $comp] != 1 } {
			continue
		} else {
			return $comp
		}
	}
	puts "$comp_name not found"
	exit 1
}

proc init_setup {} {
	# Source files required for building application
	source_extension
	# Setup parameters based on the yaml config file
	read_yaml_config
	# Set directory name where elf gets generated
	set_elf_dir_name
}

proc cleanup {} {
	if { $::params(do_cleanup) eq 1 } {
		remove "$::params(ws)/$::params(pname)/$::elf_dir_name"
		remove "$::params(ws)/$::params(pname)/src/*.c"
		remove "$::params(ws)/$::params(pname)/src/*.h"
	}
}

# Check if elf exists in the required folder path
proc verify_elf {new_elf_name default_elf_dir_path default_elf_name} {
	set data ""
	set elf_path "$default_elf_dir_path/$default_elf_name"
	set fileId [open "$::env(test_image_path)/results.txt" "a+"]
	if { [is_file "$elf_path"] } {
		copy $elf_path $::params(out_dir)/$new_elf_name
		if { "$new_elf_name" ne "$default_elf_name" } {
			file rename $elf_path $default_elf_dir_path/$new_elf_name
		}
		puts "SUCCESS: $new_elf_name ELF GENERATED"
		set data "$new_elf_name PASS"
		set ::returncode 0
	} else {
		puts "ERROR: $new_elf_name ELF GENERATION FAILED"
		set data "$new_elf_name FAIL"
	}
	puts $fileId $data
	close $fileId
}


proc download_dependency { dir_path testname download_destination } {
	if { "$::params(driver)" ne "" || "$::params(library_name)" ne "" } {
		exec python $::env(SCRIPTS_PYTHON)/download_dependency.py "$dir_path" "$testname" "$download_destination"
	}
}

proc get_example_list {dir} {

    if [file exists "$dir/data/dependencies.props" ] {
        set filelist []
        set f [open "$dir/data/dependencies.props" r]
        foreach line [split [read $f] \n] {
            lappend filelist $dir/examples/[lindex [split $line =] 0]
        }
        close $f
    } else {
        set filelist [glob -type f $dir/examples/*.c]
    }

    return $filelist
}

# build elf's for driver/libraries, if example_name is not mentioned all
# examples of provided driver/library will be build
proc build_library_driver {dir} {

    set dependent [file exists "$dir/data/dependencies.props" ]
    set filelist [get_example_list $dir]

	foreach file $filelist {
		set filename [lindex [split $file /] end]
		lassign [split $filename .] testname filetype
		if { "$::params(skip_examples)" ne "" && [lsearch $::skip_examples $testname] >= 0} {
			continue
		}
		if { "$::params(example_name)" ne "" && [lsearch $::examples $testname] < 0} {
			continue
		}

		if { ! [string match "*example*" $testname] && ! $dependent } {
			continue
		}

		remove "$::params(ws)/$::params(pname)/src/*.c"
		puts "Running the Testcase: $testname"

		copy  $file $::params(ws)/$::params(pname)/src/.

		download_dependency "$dir" "$testname" "$::params(ws)/$::params(pname)/src/"

		if { [ is_proc build_library_driver_prepend] } {
			build_library_driver_prepend
		}

		build app $::params(pname)

		if { [ is_proc build_library_driver_append] } {
			build_library_driver_append
		}

		set ::elf_name "$testname"

		copy_verify_clean
	}
}

proc build_intg_driver {dir} {
	file copy -force {*}[glob $dir/*.c] $::params(ws)/$::params(pname)/src/.
	file copy -force {*}[glob $dir/*.h] $::params(ws)/$::params(pname)/src/.
	file copy -force {*}[glob $::params(rp_intg)/XilinxProcessorIPLib/drivers/common/ct_timestamp*] $::params(ws)/$::params(pname)/src/.

	if { [ is_proc build_intg_driver_prepend] } {
		build_intg_driver_prepend
	}

	build app $::params(pname)

	if { [ is_proc build_intg_driver_append] } {
		build_intg_driver_append
	}
	copy_verify_clean
}

proc create_workspace {} {
	if { $::params(ws) ne ""} {
		# Remove workspace if exists
		remove $::params(ws)

		# Create workspace
		setws $::params(ws)

	} else {
		# Error: Workspace is needed
		puts stderr "ERROR: Workspace not mentioned"
		exit 1
	}
}

proc set_repo_path {} {
	if { $::params(rp) ne "" && [is_dir $::params(rp)] } {
		repo -set $::params(rp)
	}
}

proc get_repo_path {} {
	set repo_path [repo -get]
	puts "Repo path Set to: $repo_path"
}

proc create_hw_project {} {
	if { $::params(hdf) ne ""} {
		if {! [is_file $::params(hdf)] } {
			puts stderr "ERROR: INVALID HDF PATH"
			exit 1
		}
	} else {
		puts stderr "ERROR: NO HDF mentioned for HWPROJ generation"
		exit 1
	}

	if { $::params(pname) ne ""} {
		if { $::params(hwpname) eq ""} {
			set ::params(hwpname) "$::params(pname)\_hwproj"
		}
	} else {
		puts stderr "ERROR: Project name not mentioned"
		exit 1
	}
	platform create -name $::params(hwpname) -hw $::params(hdf)
}

proc set_processor_name {} {
	# Find all the valid processors in the HDF
	set processor [hsi::get_cells -filter {IP_TYPE==PROCESSOR}]
	if {! [contains_any $::params(processor) $processor] == "1" } {
		puts "WARN: The given processor: $::params(processor) is not supported in design, \
		using design supported processor:[lindex $processor 0]"
		set ::params(processor) [lindex $processor 0]
	}
}

proc do_bsp_config {conf} {
	#  Availabe BSP configs
	#  proc                           Processor name
	#  archiver                       Set archiver option
	#  compiler                       Set compiler
	#  compiler_flags                 Set compiler flags
	#  extra_compiler_flags           Set extra compiler flags
	#  os                             Set os
	#  stdin                          Set standard input
	#  stdout                         Set standard output
	if { [catch {xsct_config bsp [dict get $conf bsp]} result] } {
		puts "XSCTHELPER INFO: No BSP Configuration \n\t $result"
	}
}

proc do_app_config {conf} {
	# Available App Configurations
	#   assembler-flags                Miscellaneous flags for assembler
	#   build-config                   Get/set build configuration
	#   compiler-misc                  Compiler miscellaneous flags
	#   compiler-optimization          Optimization level
	#   define-compiler-symbols        Define symbols. Ex. MYSYMBOL
	#   include-path                   Include path for header files
	#   libraries                      Libraries to be added while linking
	#   library-search-path            Search path for the libraries added
	#   linker-misc                    Linker miscellaneous flags
	#   linker-script                  Linker script for linking the program sections
	#   undef-compiler-symbols         Undefine symbols. Ex. MYSYMBOL
	if { [catch {xsct_config app [dict get $conf app]} result] } {
		puts "XSCTHELPER INFO: No APP configuration \n\t $result"
	}
}

proc read_yaml_config {} {
	if { $::params(yamlconf) ne "" } {
		set ::conf_dict [::yaml::yaml2dict -file $::params(yamlconf)]
	}
}

proc verify_bsp_build {} {
	set sw_path "$::params(ws)/$::params(hwpname)/export/$::params(hwpname)/sw"
	set libxil_path "$sw_path/$::params(hwpname)/$::params(bspname)/bsplib/lib/libxil.a"
	if {! [is_file $libxil_path] } {
		puts stderr "ERROR: BSP BUILD FAILED"
	} else {
		puts "SUCCESS: BSP BUILD SUCCESSFUL"
		set ::returncode 0
	}
}

proc build_bsp {} {
	if {$::params(bspname) eq ""} {
		set ::params(bspname) "$::params(pname)\_bsp"
	}
	if {$::params(app) ne "Empty Application"} {
		domain create -name $::params(bspname) -proc $::params(processor) \
		-os $::params(osname) -support-app "$::params(app)"
	} else {
		domain create -name $::params(bspname) -proc $::params(processor) -os $::params(osname)
	}
	platform config -remove-boot-bsp
	do_armcc_config
	platform generate
	xsct_set_libs $::libs

	if { $::conf_dict ne "" } {
		do_bsp_config $::conf_dict
	}
}

proc apply_config {} {
	if { $::conf_dict ne "" && [dict exists $::conf_dict "app"] } {
		do_app_config $::conf_dict
	}
}

proc create_application {} {
	if { $::params(build_till_bsp) eq 1 } {
		get_dir_name
		verify_bsp_build
		set ::params(do_compile) "0"
		return
	}
	# Create a App for custom bsp
	app create -name $::params(pname) -plat $::params(hwpname) \
	-dom $::params(bspname) -lang c -template $::params(app)
	# set app src path as env
	set ::env(app_src) "$::params(ws)/$::params(pname)/src"
	set ::env(app_name) "$::params(pname)"
	# Apply app configuration
	apply_config
}

proc get_dir_name {} {
	set dir ""
	if {$::params(driver) ne ""} {
		set complist [compute_latest_ver "driver"]
		set driver_full_name [get_comp_name_ver $::params(driver) $complist]
		set dir "$::params(rp)/XilinxProcessorIPLib/drivers/$driver_full_name"
		if { $::params(rp_intg) ne "" } {
			if { $::params(functest_name) ne "" } {
				set dir "$::params(rp_intg)/XilinxProcessorIPLib/drivers/$::params(driver)/functionaltests/$::params(functest_name)"
			} else {
				set dir "$::params(rp_intg)/XilinxProcessorIPLib/drivers/$::params(driver)/intgtest"
			}
		}
	} elseif {$::params(library_name) ne ""} {
		set complist [compute_latest_ver "library"]
		set library_full_name [get_comp_name_ver $::params(library_name) $complist]
		set dir "$::params(rp)/lib/sw_services/$library_full_name"
	}
	return $dir
}

proc get_elf_name {} {
	set elf_name $::elf_name
	if { $::params(elf_name) ne "" } {
		set elf_name $::params(elf_name)
	}
	if { $elf_name eq "" } {
		set elf_name [ join [string tolower $::params(app)] _ ]
	}

	if { $::params(rp_intg) ne "" } {
		set elf_name [ join [string tolower $::params(driver)] _ ]
		if { $::params(functest_name) ne "" } {
			set elf_name ${elf_name}_$::params(functest_name)_functest
		} else {
			set elf_name ${elf_name}_intgtest
		}
	}

	if { [info exists ::env(TOOLCHAIN)] && $::env(TOOLCHAIN) eq "armcc" } {
		# prepending armcc to elf_name
		set elf_name armcc_${elf_name}
	}
	return "${elf_name}.elf"
}

proc compile_application {} {
	if { $::params(do_compile) eq 1 } {
		set dir [get_dir_name]
		if { $dir ne ""} {
			set ::env(esw_dir) "$dir"
			if { [is_dir $dir] && $::params(rp_intg) ne ""} {
				build_intg_driver $dir
			} elseif { [is_dir $dir] } {
				build_library_driver $dir
			}
		} else {
			if { [ is_proc build_apps_prepend ] } {
				build_apps_prepend
			}
			build app $::params(pname)
			if { [ is_proc build_apps_append ] } {
				build_apps_append
			}
			# Empty Application build do not generate any elf
			if { $::params(extension) ne "" || $::params(app) ne "Empty Application" } {
				copy_verify_clean
			}
		}
	}
}

# Make Function Calls
init_setup
create_workspace
set_tool_chain
set_repo_path
get_repo_path
create_hw_project
set_processor_name
build_bsp
create_application
compile_application

exit "$returncode"
