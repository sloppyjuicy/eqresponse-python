#!/bin/bash

selection="month"
if [ $# == 1 ]; then
  selection=$1
fi


FEEDDIR=$HOME/projects/eqresponse-python/data/feeds

if [ $selection == "month" ]; then
  curl -o ${FEEDDIR}/all_month.xml -O https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.quakeml
  curl -o ${FEEDDIR}/all_month.geojson -O https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson
elif [ $selection == "week" ]; then
  curl -o ${FEEDDIR}/all_week.xml -O https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.quakeml 
  curl -o ${FEEDDIR}/all_week.geojson -O https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson
elif [ $selection == "day" ]; then 
  curl -o ${FEEDDIR}/all_day.xml -O https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.quakeml 
  curl -o ${FEEDDIR}/all_day.geojson -O https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson
elif [ $selection == "hour" ]; then
  curl -o ${FEEDDIR}/all_hour.xml -O https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.quakeml 
  curl -o ${FEEDDIR}/all_hour.geojson -O https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson
else
  echo "Unknown selection '$selection'."
  exit 1
fi
exit 0
