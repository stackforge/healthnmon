# vim: tabstop=4 shiftwidth=4 softtabstop=4

#          (c) Copyright 2012 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

%global with_doc 0

%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%endif

Name:             healthnmon
Version:          0.0.21.5538bc3
Release:          1

Group:            Applications/System
License:          Apache
Vendor:           Hewlett Packard Company

Source0:          %{name}-0.0.21.5538bc3.tar.gz
Source1:          %{name}.init
Source2:          copyright

BuildRoot:        %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)

BuildArch:        noarch

Summary:          healthnmon Service

Requires:  python-%{name}    = %{version}
Requires:  python
Requires:  initscripts
Requires:  openstack-utils

%description
Health and Monitoring module for cloud
  The healthnmon project provides health and monitoring service for cloud.

%package -n       python-%{name}
Summary:          %{name} Python libraries
Group:            Applications/System

Requires:  python >= 2.6
Requires:  python < 2.8
Requires:  python-daemon
Requires:  python-sqlalchemy
Requires:  python-eventlet
Requires:  libxml2-python
Requires:  python-webob1.2
Requires:  python-netaddr
Requires:  python-migrate
Requires:  python-simplejson
Requires:  python-lxml
Requires:  pyxattr
Requires:  sudo
Requires:  libvirt-python
Requires:  python-paramiko 
# Requires:  python-guppy 
Requires:  python-nova >= %{version}


%description -n   python-%{name}
Health and Monitoring module for cloud
  The healthnmon project provides health and monitoring service for cloud.

  This package contains the Python libraries.

%if 0%{?with_doc}
%package doc
Summary:          healthnmon Service - Documentation
Group:            Documentation

%description      doc
healthnmon Service - Documentation
  The healthnmon project provides health and monitoring service for cloud.

  This package contains the documentation.
%endif

%post

case "$*" in
    1) # new installation
        openstack-config --set /etc/nova/nova.conf DEFAULT osapi_compute_extension healthnmon.api.healthnmon.Healthnmon
        ;;
    2) # Upgrade
        ;;
esac

exit 0;

%post -n python-%{name}
if which pycompile >/dev/null 2>&1; then
	pycompile -p python-%{name} 
fi

%preun -n python-%{name}
if which pyclean >/dev/null 2>&1; then
	pyclean -p python-%{name} 
else
	rpm -ql python-%{name} | grep \.py$ | while read file
	do
		rm -f "${file}"[co] >/dev/null
  	done
fi


%prep
%setup -q -n %{name}-%{version}

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

# Delete tests
rm -fr %{buildroot}%{python_sitelib}/tests

%if 0%{?with_doc}
export PYTHONPATH="$( pwd ):$PYTHONPATH"
pushd doc
sphinx-build -b html source build/html
popd

# Fix hidden-file-or-dir warnings
rm -fr doc/build/html/.doctrees doc/build/html/.buildinfo
%endif

# Setup directories
install -d -m 755 %{buildroot}%{_localstatedir}/run/%{name}
install -d -m 755 %{buildroot}%{_localstatedir}/log/%{name}
install -d -m 755 %{buildroot}%{_sysconfdir}/%{name}/

#  Install copyright
install -p -D -m 755 %{SOURCE2} %{buildroot}%{_docdir}/%{name}/copyright
install -p -D -m 755 %{SOURCE2} %{buildroot}%{_docdir}/python-%{name}/copyright
%if 0%{?with_doc}
install -p -D -m 755 %{SOURCE2} %{buildroot}%{_docdir}/%{name}-doc/copyright
%endif

# Initscripts
install -p -D -m 755 %{SOURCE1} %{buildroot}%{_initrddir}/%{name}

# Config files
install -p -D -m 600 etc/%{name}/logging-%{name}.conf %{buildroot}%{_sysconfdir}/%{name}/logging-%{name}.conf
install -p -D -m 600 etc/%{name}/logging-%{name}-manage.conf %{buildroot}%{_sysconfdir}/%{name}/logging-%{name}-manage.conf

%clean
# Don't remove rpmbuild directory after build.

%files
%defattr(-,root,root,-)
%dir %attr(0755, nova, nova) %{_localstatedir}/run/%{name}
%dir %attr(0755, nova, nova) %{_localstatedir}/log/%{name}
%dir %attr(0755, nova, root) %{_sysconfdir}/%{name}/
%{_sysconfdir}/%{name}/logging-%{name}-manage.conf
%{_bindir}/healthnmon
%{_bindir}/healthnmon-manage
%{_initrddir}/healthnmon
%doc %{_docdir}/%{name}/copyright
%defattr(-,nova,nova,-)
%{_sysconfdir}/%{name}/logging-%{name}.conf

%files -n python-%{name}
%defattr(-,root,root,-)
%doc %{_docdir}/python-%{name}/copyright
%{python_sitelib}/%{name}
%{python_sitelib}/%{name}-*.egg-info

%if 0%{?with_doc}
%files doc
%defattr(-,root,root,-)
%doc %{_docdir}/%{name}-doc/copyright
%doc doc/build/html
%endif

%changelog
* Fri Mar 02 2012 Divakar <dpadi@hp.com>, Ishant <ishant.tyagi@hp.com> - 2012.1
- Initial build
