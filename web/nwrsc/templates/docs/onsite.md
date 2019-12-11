# Onsite Results/Registration

## Connecting

To connect to onsite registration or results, you must connect your device to
the local WiFi for your event.  The WiFi name is usually related to the club
running the event.  There may be multiple WiFi networks onsite:

1. at the timing van which provides results 
2. possibly one at registration which allows you to create a profile and cars 

**<span style='color:red'>
Note: You may need to disable cellular data or switch to airplane mode and
then enable Wifi for some of the following things to work
</span>**


## Results

For results, if the event has an appropriate router, you can put "**de/**" into
your browser and you will be redirected to the main results page on the local
data entry machine.  Some devices may need to use "**de./**" with the extra
period.

If the event does not have this functionality, you will need to find out what
the IP address is for the data entry machine and enter that into your browser,
somthing like "**192.168.1.2**".

The results site is just like the site on the main server, select the necessary
series and event from the drop down menus.  You can then select any of the
event result pages for the event.


## Registration

For registration, if the event has an appropriate router, you can put
"**reg/**" into your browser and you will be redirected to the registration
page on a local machine running Registration.  Some devices may need to use
"**reg./**" with the extra period.

If the event does not have this functionality, you will need to find out what
the IP address is for the registation machine and enter that into your browser,
somthing like "**192.168.1.101**".

Once on the registation page, the interface is just like the main Scorekeeper
website except that you cannot actually register/unregister cars.  You can only
create and edit profiles and cars.  An example of what you can do to make the
whole registation process go faster is to create a new car entry when you
decided to drive someone elses car the day of.  The registation worker will
need to do actual registration.


## Club Setup

To enable the **de/** and **reg/** hostnames, you need to have the WiFi router
setup to so that users have their DNS set to one of the Scorekeeper machines rather
than the router itself. The target is usually the data entry machine.  This is
assuming an onsite isolated network where you don't require normal DNS services.

<span style='color:#F46700'>
Some clients may use Multicast DNS and Scorekeeper will respond to those
automatically but some will require the usual unicast DNS location to be setup.
</span>

Most routers will let you set the DNS value that DHCP serves up from one of the
adminstration pages.  As this is a static value, it would be wise to also setup
a static DHCP reservation for the machine you are pointing at.  Keep in mind
that static reservations are usually based on the MAC address and your ethernet
interface has a different MAC than your WiFi interface so want to connect the
same way each time.  If next to the router, by ethernet is best.

When this is setup, the following will happen:

 1. when the scorekeeper machine connects, it will always be given the same IP address
 1. when other devices connect, they will get a somewhat random IP address but their
    configured DNS will point to the above machine
 1. when other devices go to **de/** or **reg/**, they will query the scorekeeper
    machine which is aware of all the Scorekeeper devices on the network and which
    applications are running
 1. for **de** it looks for devices running DataEntry, for **reg** it looks for devices
    running Registration, if it can't find a match it picks a random Scorekeeper machine
    as they should all be syncing if on the same network
