#!/bin/bash

function usage {
  echo "  -c,    Run Unit Test Cases"
  echo "  -t,    Create Healthnmon Tarball"
  echo "  -r,    Create Healthnmon RPM"
  echo "  -d,    Create Healthnmon DEBIAN"
  exit
}

create_rpm=0
create_tar=0
create_deb=0
run_tests=0

if [[ $# -eq 0 ]]
then
    usage
    exit 1
fi

while getopts "ctrd" OPTION
do
   case $OPTION in
      c)
         run_tests=1
         ;;
      t)
         create_tar=1
         ;;
      r)
         create_tar=1
         create_rpm=1
         ;;
      d)
         create_tar=1
         create_deb=1
         ;;
      ?)
         usage
         exit 1
         ;;
   esac
done


if [ $run_tests -eq 1 ]; then
    tox -epy26
    status=$?
    if [[ $status -ne 0 ]]
    then
      exit 1
    fi
fi

if [ $create_tar -eq 1 ]; then
  rm -rf healthnmon/versioninfo
  python setup.py sdist
  status=$?
  if [[ $status -ne 0 ]]
  then
     echo "Error: Failed to create healthnmon tar"
     exit 1
  else
     echo "Successfully created healthnmon tar."
  fi
fi

if [ $create_rpm -eq 1 ]; then
    ver=`python rpm_util.py`
    rpmBuildPath=`pwd`/target/rpmbuild
	rm -rf $rpmBuildPath
	
	mkdir -p $rpmBuildPath/SOURCES
	cp dist/healthnmon-$ver.tar.gz $rpmBuildPath/SOURCES
	cp rpm/healthnmon.init $rpmBuildPath/SOURCES
	cp rpm/copyright $rpmBuildPath/SOURCES
	
	rpmbuild --define "_topdir $rpmBuildPath" --define "ver $ver" --define "release `date +%Y%m%d.%H%M%S`" -ba rpm/healthnmon.spec
	status=$?
	if [[ $status -ne 0 ]]
    then
       echo "Error: Failed to create healthnmon RPM"
       exit 1
    else
       echo "Successfully created healthnmon RPM."
    fi
fi

if [ $create_deb -eq 1 ]; then
   tarPath=`pwd`/dist/healthnmon-*.tar.gz
   python builddeb.py $tarPath "Changelog comments"
   status=$?
   if [[ $status -ne 0 ]]
   then
   	echo "Error: Failed to create healthnmon DEBIAN"
   	exit 1
   else
       echo "Successfully created healthnmon DEBIAN."
   fi
fi
