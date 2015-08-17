startdate = raw_input("Enter the start date in DD-MMM-YYYY format (i.e. 01-Aug-2015): ")
enddate = raw_input("Enter the end date in DD-MMM-YYYY format (i.e. 01-Aug-2015): ")
searchquery = "SINCE \"%s\" BEFORE \"%s\"" % (startdate, enddate)
print searchquery