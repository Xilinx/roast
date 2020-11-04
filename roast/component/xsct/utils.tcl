# Return value if key exists, else return empty string
proc get_key_value { dict key } {
	if { [ dict exists $dict $key ] } {
		return [ dict get $dict $key ]
	}
}

# Delete the file/directory if exists else ignore
proc remove {path} {
	catch {file delete -force {*}[glob -nocomplain $path]}
}

# Return 1 if item found, else return 0
proc contains_any {item item_list} {
	foreach li $item_list {
		if { [string match $li $item] } {
			return 1
		}
	}
	return 0
}

# If dir return 1 else return 0
proc is_dir {path} {
	return [file isdirectory "$path"]
}

# If file return 1 else return 0
proc is_file {path} {
	return [file isfile $path]
}

# Copy the file from source to destination else reports error
proc copy {src dest} {
	if { [file exists $src] } {
		file copy -force $src $dest
	} else {
		puts "ERROR : $src does not exists"
	}
}

# Check if the procedure exists in the current namespace
proc is_proc p {
	return [expr {[llength [info procs $p]] > 0}]
}
