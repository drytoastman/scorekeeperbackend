
# Recommended Setups

The frontend pieces run on top of Java and are relatively platform agnostic
expect for items such as serial port access.

The backend pieces run in Docker containers to maintain the same behavior
everywhere.  The Docker requirement is the primary driver of the below
recommendations.

## 1. Linux

The cheapest and lightest weight setup would a simple Linux install as docker
runs natively here.  I find that installing Debian with the XFCE desktop to be
the quickest to boot and shutdown as it doesn't have all the extra visual bells
and whistles that you don't use.

Pros:

  * Native Docker
  * Lowest resorce usage
  * Free
  * should not require CPU virtualization extensions (though most have them now)


Cons:

  * Different interafce than Windows/OS X
  * Maybe not ideal if laptop has dual use outside of events


## 2. Windows 10 (After Summer 2020 update)

When Microsoft realease their 20H1 update in the summer of 2020, they will have
a new version of the Windows Subsystem for Linux.  This lightweight
virtualization is actually running a regular Linux kernel and is capable of
running Docker.  Best of all, it looks like it will even be available for Home
editions of Windows.

Pros:

  * Almost native Docker
  * Still pretty lightweight
  * Still have Windows 10 stuff for non-event use

Cons:

  * Not free (though most laptops come with Windows)


## 3. Windows 10 Professional or OS X

Both of the these allow installation of Docker Desktop via a slightly heavier
weight virtual machines.  Hyper-V for Windows and Hypervisor.framework for OS
X.

Pros:

  * Faster to start than Docker-Toolbox installs
  * Available now for newer OS versions
  * Still have normal OS stuff for non-event usage

Cons:

  * middleweight VM, takes some time to start up but is managed as a service
  * more resource usage then 1 or 2


## 4. Older Windows or OS X Machines

Older machines require the use of Docker-Toolbox and VirtualBox.  VirtualBox is
a complete viritualization solution.

Pros:

  * Can work on older OS X or Windows versions

Cons:

  * most memory and CPU overhead
  * VM is slow to boot

