#!/usr/bin/env python3
"""GeoSentinel 2.0 Scanner v2 — Multi-source disease surveillance with anomaly detection.
Sources: WHO, Twitter/X, Reddit, Google Trends, News, ProMED
Features: deduplication, traveler detection, anomaly scoring, city-level geocoding"""

import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.parse
import hashlib
import gzip
from datetime import datetime, timezone, timedelta
from collections import defaultdict

DIR = os.path.dirname(os.path.abspath(__file__))
SIGNALS_FILE = os.path.join(DIR, "terminal", "signals.json")
HISTORY_FILE = os.path.join(DIR, "signal_history.json")

# ═══════════════════════════════════════════
# GEOCODING DATABASE — City + Country level
# ═══════════════════════════════════════════
GEO_DB = [
    # Cities first (more specific = higher priority)
    {"keys":["chiang mai"],"lat":18.79,"lng":98.98,"name":"Chiang Mai","country":"Thailand","iso":"TH","region":"SE Asia"},
    {"keys":["phuket"],"lat":7.88,"lng":98.39,"name":"Phuket","country":"Thailand","iso":"TH","region":"SE Asia"},
    {"keys":["bangkok"],"lat":13.75,"lng":100.5,"name":"Bangkok","country":"Thailand","iso":"TH","region":"SE Asia"},
    {"keys":["bali","denpasar"],"lat":-8.34,"lng":115.09,"name":"Bali","country":"Indonesia","iso":"ID","region":"SE Asia"},
    {"keys":["jakarta"],"lat":-6.21,"lng":106.85,"name":"Jakarta","country":"Indonesia","iso":"ID","region":"SE Asia"},
    {"keys":["hanoi"],"lat":21.03,"lng":105.85,"name":"Hanoi","country":"Vietnam","iso":"VN","region":"SE Asia"},
    {"keys":["ho chi minh","saigon"],"lat":10.82,"lng":106.63,"name":"Ho Chi Minh City","country":"Vietnam","iso":"VN","region":"SE Asia"},
    {"keys":["phnom penh"],"lat":11.56,"lng":104.92,"name":"Phnom Penh","country":"Cambodia","iso":"KH","region":"SE Asia"},
    {"keys":["siem reap"],"lat":13.36,"lng":103.86,"name":"Siem Reap","country":"Cambodia","iso":"KH","region":"SE Asia"},
    {"keys":["manila"],"lat":14.60,"lng":120.98,"name":"Manila","country":"Philippines","iso":"PH","region":"SE Asia"},
    {"keys":["kuala lumpur"],"lat":3.14,"lng":101.69,"name":"Kuala Lumpur","country":"Malaysia","iso":"MY","region":"SE Asia"},
    {"keys":["delhi","new delhi"],"lat":28.61,"lng":77.21,"name":"Delhi","country":"India","iso":"IN","region":"South Asia"},
    {"keys":["mumbai","bombay"],"lat":19.07,"lng":72.88,"name":"Mumbai","country":"India","iso":"IN","region":"South Asia"},
    {"keys":["goa"],"lat":15.30,"lng":74.12,"name":"Goa","country":"India","iso":"IN","region":"South Asia"},
    {"keys":["kolkata","calcutta"],"lat":22.57,"lng":88.36,"name":"Kolkata","country":"India","iso":"IN","region":"South Asia"},
    {"keys":["chennai","madras"],"lat":13.08,"lng":80.27,"name":"Chennai","country":"India","iso":"IN","region":"South Asia"},
    {"keys":["kathmandu"],"lat":27.72,"lng":85.32,"name":"Kathmandu","country":"Nepal","iso":"NP","region":"South Asia"},
    {"keys":["dhaka","dacca"],"lat":23.81,"lng":90.41,"name":"Dhaka","country":"Bangladesh","iso":"BD","region":"South Asia"},
    {"keys":["colombo"],"lat":6.93,"lng":79.84,"name":"Colombo","country":"Sri Lanka","iso":"LK","region":"South Asia"},
    {"keys":["cancun","cancún"],"lat":21.16,"lng":-86.85,"name":"Cancún","country":"Mexico","iso":"MX","region":"Latin America"},
    {"keys":["mexico city","ciudad de mexico"],"lat":19.43,"lng":-99.13,"name":"Mexico City","country":"Mexico","iso":"MX","region":"Latin America"},
    {"keys":["lima"],"lat":-12.05,"lng":-77.04,"name":"Lima","country":"Peru","iso":"PE","region":"Latin America"},
    {"keys":["cusco","cuzco"],"lat":-13.53,"lng":-71.97,"name":"Cusco","country":"Peru","iso":"PE","region":"Latin America"},
    {"keys":["bogota","bogotá"],"lat":4.71,"lng":-74.07,"name":"Bogotá","country":"Colombia","iso":"CO","region":"Latin America"},
    {"keys":["cartagena"],"lat":10.39,"lng":-75.51,"name":"Cartagena","country":"Colombia","iso":"CO","region":"Latin America"},
    {"keys":["rio de janeiro","rio"],"lat":-22.91,"lng":-43.17,"name":"Rio de Janeiro","country":"Brazil","iso":"BR","region":"Latin America"},
    {"keys":["sao paulo","são paulo"],"lat":-23.55,"lng":-46.63,"name":"São Paulo","country":"Brazil","iso":"BR","region":"Latin America"},
    {"keys":["buenos aires"],"lat":-34.60,"lng":-58.38,"name":"Buenos Aires","country":"Argentina","iso":"AR","region":"Latin America"},
    {"keys":["nairobi"],"lat":-1.29,"lng":36.82,"name":"Nairobi","country":"Kenya","iso":"KE","region":"East Africa"},
    {"keys":["mombasa"],"lat":-4.05,"lng":39.67,"name":"Mombasa","country":"Kenya","iso":"KE","region":"East Africa"},
    {"keys":["dar es salaam"],"lat":-6.79,"lng":39.28,"name":"Dar es Salaam","country":"Tanzania","iso":"TZ","region":"East Africa"},
    {"keys":["zanzibar"],"lat":-6.17,"lng":39.20,"name":"Zanzibar","country":"Tanzania","iso":"TZ","region":"East Africa"},
    {"keys":["kampala"],"lat":0.35,"lng":32.58,"name":"Kampala","country":"Uganda","iso":"UG","region":"East Africa"},
    {"keys":["addis ababa"],"lat":9.02,"lng":38.75,"name":"Addis Ababa","country":"Ethiopia","iso":"ET","region":"East Africa"},
    {"keys":["kigali"],"lat":-1.97,"lng":30.10,"name":"Kigali","country":"Rwanda","iso":"RW","region":"East Africa"},
    {"keys":["kinshasa"],"lat":-4.44,"lng":15.27,"name":"Kinshasa","country":"DR Congo","iso":"CD","region":"Central Africa"},
    {"keys":["lagos"],"lat":6.52,"lng":3.38,"name":"Lagos","country":"Nigeria","iso":"NG","region":"West Africa"},
    {"keys":["accra"],"lat":5.60,"lng":-0.19,"name":"Accra","country":"Ghana","iso":"GH","region":"West Africa"},
    {"keys":["dakar"],"lat":14.69,"lng":-17.44,"name":"Dakar","country":"Senegal","iso":"SN","region":"West Africa"},
    {"keys":["cairo"],"lat":30.04,"lng":31.24,"name":"Cairo","country":"Egypt","iso":"EG","region":"North Africa"},
    {"keys":["marrakech","marrakesh"],"lat":31.63,"lng":-8.01,"name":"Marrakech","country":"Morocco","iso":"MA","region":"North Africa"},
    {"keys":["cape town"],"lat":-33.93,"lng":18.42,"name":"Cape Town","country":"South Africa","iso":"ZA","region":"Southern Africa"},
    {"keys":["johannesburg"],"lat":-26.20,"lng":28.05,"name":"Johannesburg","country":"South Africa","iso":"ZA","region":"Southern Africa"},
    {"keys":["beijing","peking"],"lat":39.90,"lng":116.41,"name":"Beijing","country":"China","iso":"CN","region":"East Asia"},
    {"keys":["shanghai"],"lat":31.23,"lng":121.47,"name":"Shanghai","country":"China","iso":"CN","region":"East Asia"},
    {"keys":["hong kong"],"lat":22.32,"lng":114.17,"name":"Hong Kong","country":"China","iso":"CN","region":"East Asia"},
    {"keys":["tokyo"],"lat":35.68,"lng":139.69,"name":"Tokyo","country":"Japan","iso":"JP","region":"East Asia"},
    {"keys":["singapore"],"lat":1.35,"lng":103.82,"name":"Singapore","country":"Singapore","iso":"SG","region":"SE Asia"},
    {"keys":["sydney"],"lat":-33.87,"lng":151.21,"name":"Sydney","country":"Australia","iso":"AU","region":"Oceania"},
    {"keys":["istanbul"],"lat":41.01,"lng":28.98,"name":"Istanbul","country":"Turkey","iso":"TR","region":"Middle East"},
    {"keys":["dubai"],"lat":25.20,"lng":55.27,"name":"Dubai","country":"UAE","iso":"AE","region":"Middle East"},
    # Countries (fallback)
    {"keys":["thailand"],"lat":13.75,"lng":100.5,"name":"Thailand","country":"Thailand","iso":"TH","region":"SE Asia"},
    {"keys":["indonesia"],"lat":-2.5,"lng":118.0,"name":"Indonesia","country":"Indonesia","iso":"ID","region":"SE Asia"},
    {"keys":["vietnam"],"lat":14.06,"lng":108.28,"name":"Vietnam","country":"Vietnam","iso":"VN","region":"SE Asia"},
    {"keys":["cambodia"],"lat":12.57,"lng":104.99,"name":"Cambodia","country":"Cambodia","iso":"KH","region":"SE Asia"},
    {"keys":["philippines"],"lat":12.88,"lng":121.77,"name":"Philippines","country":"Philippines","iso":"PH","region":"SE Asia"},
    {"keys":["malaysia"],"lat":4.21,"lng":101.98,"name":"Malaysia","country":"Malaysia","iso":"MY","region":"SE Asia"},
    {"keys":["myanmar","burma"],"lat":21.91,"lng":95.96,"name":"Myanmar","country":"Myanmar","iso":"MM","region":"SE Asia"},
    {"keys":["laos"],"lat":19.86,"lng":102.50,"name":"Laos","country":"Laos","iso":"LA","region":"SE Asia"},
    {"keys":["india"],"lat":20.59,"lng":78.96,"name":"India","country":"India","iso":"IN","region":"South Asia"},
    {"keys":["nepal"],"lat":28.39,"lng":84.12,"name":"Nepal","country":"Nepal","iso":"NP","region":"South Asia"},
    {"keys":["bangladesh"],"lat":23.68,"lng":90.36,"name":"Bangladesh","country":"Bangladesh","iso":"BD","region":"South Asia"},
    {"keys":["sri lanka"],"lat":7.87,"lng":80.77,"name":"Sri Lanka","country":"Sri Lanka","iso":"LK","region":"South Asia"},
    {"keys":["pakistan"],"lat":30.38,"lng":69.35,"name":"Pakistan","country":"Pakistan","iso":"PK","region":"South Asia"},
    {"keys":["afghanistan"],"lat":33.94,"lng":67.71,"name":"Afghanistan","country":"Afghanistan","iso":"AF","region":"South Asia"},
    {"keys":["mexico"],"lat":23.63,"lng":-102.55,"name":"Mexico","country":"Mexico","iso":"MX","region":"Latin America"},
    {"keys":["brazil"],"lat":-14.24,"lng":-51.93,"name":"Brazil","country":"Brazil","iso":"BR","region":"Latin America"},
    {"keys":["peru"],"lat":-9.19,"lng":-75.02,"name":"Peru","country":"Peru","iso":"PE","region":"Latin America"},
    {"keys":["colombia"],"lat":4.57,"lng":-74.3,"name":"Colombia","country":"Colombia","iso":"CO","region":"Latin America"},
    {"keys":["ecuador"],"lat":-1.83,"lng":-78.18,"name":"Ecuador","country":"Ecuador","iso":"EC","region":"Latin America"},
    {"keys":["bolivia"],"lat":-16.29,"lng":-63.59,"name":"Bolivia","country":"Bolivia","iso":"BO","region":"Latin America"},
    {"keys":["argentina"],"lat":-38.42,"lng":-63.62,"name":"Argentina","country":"Argentina","iso":"AR","region":"Latin America"},
    {"keys":["chile"],"lat":-35.68,"lng":-71.54,"name":"Chile","country":"Chile","iso":"CL","region":"Latin America"},
    {"keys":["venezuela"],"lat":6.42,"lng":-66.59,"name":"Venezuela","country":"Venezuela","iso":"VE","region":"Latin America"},
    {"keys":["costa rica"],"lat":9.75,"lng":-83.75,"name":"Costa Rica","country":"Costa Rica","iso":"CR","region":"Latin America"},
    {"keys":["guatemala"],"lat":15.78,"lng":-90.23,"name":"Guatemala","country":"Guatemala","iso":"GT","region":"Latin America"},
    {"keys":["honduras"],"lat":15.20,"lng":-86.24,"name":"Honduras","country":"Honduras","iso":"HN","region":"Latin America"},
    {"keys":["panama"],"lat":8.54,"lng":-80.78,"name":"Panama","country":"Panama","iso":"PA","region":"Latin America"},
    {"keys":["dominican republic"],"lat":18.74,"lng":-70.16,"name":"Dominican Republic","country":"Dominican Republic","iso":"DO","region":"Caribbean"},
    {"keys":["haiti"],"lat":18.97,"lng":-72.29,"name":"Haiti","country":"Haiti","iso":"HT","region":"Caribbean"},
    {"keys":["cuba"],"lat":21.52,"lng":-77.78,"name":"Cuba","country":"Cuba","iso":"CU","region":"Caribbean"},
    {"keys":["jamaica"],"lat":18.11,"lng":-77.30,"name":"Jamaica","country":"Jamaica","iso":"JM","region":"Caribbean"},
    {"keys":["kenya"],"lat":-0.02,"lng":37.91,"name":"Kenya","country":"Kenya","iso":"KE","region":"East Africa"},
    {"keys":["tanzania"],"lat":-6.37,"lng":34.89,"name":"Tanzania","country":"Tanzania","iso":"TZ","region":"East Africa"},
    {"keys":["uganda"],"lat":1.37,"lng":32.29,"name":"Uganda","country":"Uganda","iso":"UG","region":"East Africa"},
    {"keys":["rwanda"],"lat":-1.94,"lng":29.87,"name":"Rwanda","country":"Rwanda","iso":"RW","region":"East Africa"},
    {"keys":["ethiopia"],"lat":9.15,"lng":40.49,"name":"Ethiopia","country":"Ethiopia","iso":"ET","region":"East Africa"},
    {"keys":["south africa"],"lat":-30.56,"lng":22.94,"name":"South Africa","country":"South Africa","iso":"ZA","region":"Southern Africa"},
    {"keys":["nigeria"],"lat":9.08,"lng":7.49,"name":"Nigeria","country":"Nigeria","iso":"NG","region":"West Africa"},
    {"keys":["ghana"],"lat":7.95,"lng":-1.02,"name":"Ghana","country":"Ghana","iso":"GH","region":"West Africa"},
    {"keys":["senegal"],"lat":14.50,"lng":-14.45,"name":"Senegal","country":"Senegal","iso":"SN","region":"West Africa"},
    {"keys":["cameroon"],"lat":7.37,"lng":12.35,"name":"Cameroon","country":"Cameroon","iso":"CM","region":"West Africa"},
    {"keys":["ivory coast","cote d'ivoire","côte d'ivoire"],"lat":7.54,"lng":-5.55,"name":"Ivory Coast","country":"Ivory Coast","iso":"CI","region":"West Africa"},
    {"keys":["guinea"],"lat":9.95,"lng":-9.70,"name":"Guinea","country":"Guinea","iso":"GN","region":"West Africa"},
    {"keys":["sierra leone"],"lat":8.46,"lng":-11.78,"name":"Sierra Leone","country":"Sierra Leone","iso":"SL","region":"West Africa"},
    {"keys":["liberia"],"lat":6.43,"lng":-9.43,"name":"Liberia","country":"Liberia","iso":"LR","region":"West Africa"},
    {"keys":["mali"],"lat":17.57,"lng":-4.00,"name":"Mali","country":"Mali","iso":"ML","region":"West Africa"},
    {"keys":["congo","drc","democratic republic"],"lat":-4.04,"lng":21.76,"name":"DRC","country":"DR Congo","iso":"CD","region":"Central Africa"},
    {"keys":["egypt"],"lat":26.82,"lng":30.80,"name":"Egypt","country":"Egypt","iso":"EG","region":"North Africa"},
    {"keys":["morocco"],"lat":31.79,"lng":-7.09,"name":"Morocco","country":"Morocco","iso":"MA","region":"North Africa"},
    {"keys":["sudan"],"lat":12.86,"lng":30.22,"name":"Sudan","country":"Sudan","iso":"SD","region":"East Africa"},
    {"keys":["south sudan"],"lat":6.88,"lng":31.31,"name":"South Sudan","country":"South Sudan","iso":"SS","region":"East Africa"},
    {"keys":["somalia"],"lat":5.15,"lng":46.20,"name":"Somalia","country":"Somalia","iso":"SO","region":"East Africa"},
    {"keys":["chad"],"lat":15.45,"lng":18.73,"name":"Chad","country":"Chad","iso":"TD","region":"Central Africa"},
    {"keys":["central african republic","car"],"lat":6.61,"lng":20.94,"name":"CAR","country":"Central African Republic","iso":"CF","region":"Central Africa"},
    {"keys":["angola"],"lat":-11.20,"lng":17.87,"name":"Angola","country":"Angola","iso":"AO","region":"Southern Africa"},
    {"keys":["mozambique"],"lat":-18.67,"lng":35.53,"name":"Mozambique","country":"Mozambique","iso":"MZ","region":"Southern Africa"},
    {"keys":["zambia"],"lat":-13.13,"lng":27.85,"name":"Zambia","country":"Zambia","iso":"ZM","region":"Southern Africa"},
    {"keys":["zimbabwe"],"lat":-19.02,"lng":29.15,"name":"Zimbabwe","country":"Zimbabwe","iso":"ZW","region":"Southern Africa"},
    {"keys":["malawi"],"lat":-13.25,"lng":34.30,"name":"Malawi","country":"Malawi","iso":"MW","region":"Southern Africa"},
    {"keys":["madagascar"],"lat":-18.77,"lng":46.87,"name":"Madagascar","country":"Madagascar","iso":"MG","region":"East Africa"},
    {"keys":["china"],"lat":35.86,"lng":104.20,"name":"China","country":"China","iso":"CN","region":"East Asia"},
    {"keys":["japan"],"lat":36.20,"lng":138.25,"name":"Japan","country":"Japan","iso":"JP","region":"East Asia"},
    {"keys":["south korea","korea"],"lat":35.91,"lng":127.77,"name":"South Korea","country":"South Korea","iso":"KR","region":"East Asia"},
    {"keys":["australia"],"lat":-25.27,"lng":133.78,"name":"Australia","country":"Australia","iso":"AU","region":"Oceania"},
    {"keys":["fiji"],"lat":-17.71,"lng":178.07,"name":"Fiji","country":"Fiji","iso":"FJ","region":"Oceania"},
    {"keys":["turkey"],"lat":38.96,"lng":35.24,"name":"Turkey","country":"Turkey","iso":"TR","region":"Middle East"},
    {"keys":["iraq"],"lat":33.22,"lng":43.68,"name":"Iraq","country":"Iraq","iso":"IQ","region":"Middle East"},
    {"keys":["yemen"],"lat":15.55,"lng":48.52,"name":"Yemen","country":"Yemen","iso":"YE","region":"Middle East"},
    {"keys":["saudi arabia"],"lat":23.89,"lng":45.08,"name":"Saudi Arabia","country":"Saudi Arabia","iso":"SA","region":"Middle East"},
    {"keys":["italy"],"lat":41.87,"lng":12.57,"name":"Italy","country":"Italy","iso":"IT","region":"Europe"},
    {"keys":["spain"],"lat":40.46,"lng":-3.75,"name":"Spain","country":"Spain","iso":"ES","region":"Europe"},
    {"keys":["france"],"lat":46.23,"lng":2.21,"name":"France","country":"France","iso":"FR","region":"Europe"},
    {"keys":["germany"],"lat":51.17,"lng":10.45,"name":"Germany","country":"Germany","iso":"DE","region":"Europe"},
    {"keys":["uk","united kingdom","britain","england"],"lat":55.38,"lng":-3.44,"name":"UK","country":"United Kingdom","iso":"GB","region":"Europe"},
    {"keys":["greece"],"lat":39.07,"lng":21.82,"name":"Greece","country":"Greece","iso":"GR","region":"Europe"},
    {"keys":["portugal"],"lat":39.40,"lng":-8.22,"name":"Portugal","country":"Portugal","iso":"PT","region":"Europe"},
    {"keys":["mauritania"],"lat":21.01,"lng":-10.94,"name":"Mauritania","country":"Mauritania","iso":"MR","region":"West Africa"},
]

DISEASES = {
    "nipah": {"cat": "viral", "sev": 9, "emoji": "🦇"},
    "ebola": {"cat": "hemorrhagic", "sev": 10, "emoji": "🩸"},
    "marburg": {"cat": "hemorrhagic", "sev": 10, "emoji": "🩸"},
    "dengue": {"cat": "vector-borne", "sev": 6, "emoji": "🦟"},
    "malaria": {"cat": "vector-borne", "sev": 7, "emoji": "🦟"},
    "cholera": {"cat": "waterborne", "sev": 8, "emoji": "💧"},
    "typhoid": {"cat": "waterborne", "sev": 6, "emoji": "💧"},
    "zika": {"cat": "vector-borne", "sev": 5, "emoji": "🦟"},
    "chikungunya": {"cat": "vector-borne", "sev": 5, "emoji": "🦟"},
    "yellow fever": {"cat": "vector-borne", "sev": 8, "emoji": "🦟"},
    "avian flu": {"cat": "respiratory", "sev": 8, "emoji": "🐦"},
    "h5n1": {"cat": "respiratory", "sev": 8, "emoji": "🐦"},
    "bird flu": {"cat": "respiratory", "sev": 8, "emoji": "🐦"},
    "h5n6": {"cat": "respiratory", "sev": 8, "emoji": "🐦"},
    "mpox": {"cat": "viral", "sev": 5, "emoji": "🦠"},
    "monkeypox": {"cat": "viral", "sev": 5, "emoji": "🦠"},
    "measles": {"cat": "vaccine-preventable", "sev": 6, "emoji": "💉"},
    "diphtheria": {"cat": "vaccine-preventable", "sev": 7, "emoji": "💉"},
    "polio": {"cat": "vaccine-preventable", "sev": 9, "emoji": "💉"},
    "tuberculosis": {"cat": "respiratory", "sev": 7, "emoji": "🫁"},
    "tb ": {"cat": "respiratory", "sev": 7, "emoji": "🫁"},
    "plague": {"cat": "bacterial", "sev": 9, "emoji": "☠️"},
    "anthrax": {"cat": "bacterial", "sev": 8, "emoji": "☠️"},
    "meningitis": {"cat": "bacterial", "sev": 7, "emoji": "🧠"},
    "rift valley fever": {"cat": "vector-borne", "sev": 7, "emoji": "🦟"},
    "lassa fever": {"cat": "hemorrhagic", "sev": 8, "emoji": "🩸"},
    "lassa": {"cat": "hemorrhagic", "sev": 8, "emoji": "🩸"},
    "rabies": {"cat": "viral", "sev": 9, "emoji": "🐕"},
    "hepatitis a": {"cat": "waterborne", "sev": 5, "emoji": "💧"},
    "hepatitis e": {"cat": "waterborne", "sev": 5, "emoji": "💧"},
    "norovirus": {"cat": "waterborne", "sev": 4, "emoji": "💧"},
    "leptospirosis": {"cat": "waterborne", "sev": 5, "emoji": "💧"},
    "schistosomiasis": {"cat": "parasitic", "sev": 4, "emoji": "🪱"},
    "leishmaniasis": {"cat": "parasitic", "sev": 5, "emoji": "🪱"},
    "chagas": {"cat": "parasitic", "sev": 6, "emoji": "🪱"},
    "covid": {"cat": "respiratory", "sev": 5, "emoji": "🦠"},
    "sars": {"cat": "respiratory", "sev": 8, "emoji": "🦠"},
    "mers": {"cat": "respiratory", "sev": 8, "emoji": "🦠"},
    "gastroenteritis": {"cat": "waterborne", "sev": 3, "emoji": "💧"},
    "food poisoning": {"cat": "waterborne", "sev": 3, "emoji": "💧"},
    "diarrhea": {"cat": "waterborne", "sev": 3, "emoji": "💧"},
    "diarrhoea": {"cat": "waterborne", "sev": 3, "emoji": "💧"},
    "fever": {"cat": "unknown", "sev": 4, "emoji": "🌡️"},
    "hiv": {"cat": "viral", "sev": 7, "emoji": "🔴"},
}

# ═══ Major international airport hubs by country ═══
FLIGHT_HUBS = {
    "BD": [{"city":"Dhaka","lat":23.81,"lng":90.41,"iata":"DAC","routes":["DEL","DXB","KUL","SIN","DOH"]}],
    "IN": [{"city":"Delhi","lat":28.61,"lng":77.21,"iata":"DEL","routes":["DXB","LHR","SIN","BKK","JFK"]},
           {"city":"Mumbai","lat":19.07,"lng":72.88,"iata":"BOM","routes":["DXB","LHR","SIN","DOH","JFK"]}],
    "ET": [{"city":"Addis Ababa","lat":9.02,"lng":38.75,"iata":"ADD","routes":["DXB","JNB","NBO","LHR","CDG"]}],
    "CD": [{"city":"Kinshasa","lat":-4.44,"lng":15.27,"iata":"FIH","routes":["ADD","NBO","JNB","BRU","CDG"]}],
    "KH": [{"city":"Phnom Penh","lat":11.56,"lng":104.92,"iata":"PNH","routes":["BKK","SIN","ICN","HKG","KUL"]}],
    "TH": [{"city":"Bangkok","lat":13.75,"lng":100.5,"iata":"BKK","routes":["SIN","HKG","NRT","ICN","LHR"]}],
    "SN": [{"city":"Dakar","lat":14.69,"lng":-17.44,"iata":"DSS","routes":["CDG","CMN","ADD","LIS","MAD"]}],
    "NG": [{"city":"Lagos","lat":6.52,"lng":3.38,"iata":"LOS","routes":["LHR","DXB","ADD","JNB","CDG"]}],
    "KE": [{"city":"Nairobi","lat":-1.29,"lng":36.82,"iata":"NBO","routes":["ADD","DXB","LHR","JNB","BKK"]}],
    "BR": [{"city":"São Paulo","lat":-23.55,"lng":-46.63,"iata":"GRU","routes":["MIA","JFK","LHR","CDG","EZE"]}],
    "MX": [{"city":"Mexico City","lat":19.43,"lng":-99.13,"iata":"MEX","routes":["LAX","MIA","JFK","MAD","BOG"]}],
    "CN": [{"city":"Beijing","lat":39.90,"lng":116.41,"iata":"PEK","routes":["ICN","NRT","SIN","LHR","JFK"]}],
    "ZA": [{"city":"Johannesburg","lat":-26.20,"lng":28.05,"iata":"JNB","routes":["LHR","DXB","ADD","NBO","CDG"]}],
}

IATA_COORDS = {
    "DEL":(28.61,77.21),"DXB":(25.25,55.36),"LHR":(51.47,-0.46),"SIN":(1.35,103.99),
    "BKK":(13.69,100.75),"JFK":(40.64,-73.78),"CDG":(49.01,2.55),"NRT":(35.76,140.39),
    "ICN":(37.46,126.44),"HKG":(22.31,113.92),"KUL":(2.74,101.70),"DOH":(25.26,51.57),
    "NBO":(-1.32,36.93),"JNB":(-26.14,28.25),"ADD":(8.98,38.80),"BRU":(50.90,4.48),
    "MIA":(25.79,-80.29),"LAX":(33.94,-118.41),"MAD":(40.47,-3.57),"LIS":(38.77,-9.13),
    "CMN":(33.37,-7.59),"GRU":(-23.43,-46.47),"EZE":(-34.82,-58.54),"BOG":(4.70,-74.15),
    "PNH":(11.55,104.84),"DAC":(23.84,90.40),"DSS":(14.74,-17.49),"LOS":(6.58,3.32),
    "BOM":(19.09,72.87),"FIH":(-4.39,15.44),"MEX":(19.44,-99.07),"PEK":(40.08,116.58),
}

# ═══ Traveler signal patterns ═══
TRAVELER_PATTERNS = [
    r"(?:came|got|returned?|back|arrived)\s+(?:from|back from)\s+\w+.*(?:sick|ill|fever|diarr|vomit|infected|hospital)",
    r"(?:sick|ill|fever|diarr|vomit|infected)\s+(?:after|since|from)\s+(?:my |our |a )?(?:trip|travel|vacation|holiday|visit)",
    r"(?:travel|trip|vacation|holiday)\s+(?:to|in)\s+\w+.*(?:sick|ill|fever|diarr|outbreak|warning|alert)",
    r"(?:don'?t |do not )?(?:travel|go|visit)\s+(?:to )?\w+.*(?:outbreak|disease|infection|epidemic|cases)",
    r"(?:outbreak|epidemic|cases|deaths?|infections?)\s+(?:in|reported in|confirmed in|spreading in)",
    r"(?:WHO|CDC|health authority|ministry of health).*(?:warn|alert|declare|confirm|report)",
    r"(?:traveler|tourist|visitor|passenger)s?\s+(?:sick|ill|infected|diagnosed|hospitalized|quarantine)",
    r"(?:airport|border|flight|cruise)\s+(?:screen|check|quarantine|ban|restrict)",
]

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:12]

def geocode(text):
    """City-level geocoding with priority to more specific matches."""
    t = text.lower()
    for entry in GEO_DB:
        for key in entry["keys"]:
            if key in t:
                return {
                    "lat": entry["lat"], "lng": entry["lng"],
                    "name": entry["name"], "country": entry["country"],
                    "iso": entry["iso"], "region": entry.get("region", "")
                }
    return None

def detect_diseases(text):
    """Detect disease mentions, return sorted by severity."""
    t = text.lower()
    found = []
    seen = set()
    for name, info in sorted(DISEASES.items(), key=lambda x: -len(x[0])):
        if name in t and info["cat"] not in seen:
            found.append({"name": name.strip(), "cat": info["cat"], "sev": info["sev"], "emoji": info["emoji"]})
            seen.add(name.strip())
    return sorted(found, key=lambda d: -d["sev"])

def is_traveler_signal(text):
    """Check if text describes a traveler-specific health signal."""
    t = text.lower()
    for pat in TRAVELER_PATTERNS:
        if re.search(pat, t):
            return True
    return False

def compute_confidence(signal):
    """Multi-factor confidence scoring."""
    base = {"who": 0.95, "news": 0.70, "twitter": 0.45, "reddit": 0.40, "trends": 0.50}
    conf = base.get(signal.get("source", ""), 0.5)
    if signal.get("is_traveler"): conf += 0.1
    if signal.get("type") == "official_alert": conf += 0.1
    if "outbreak" in signal.get("summary", "").lower(): conf += 0.05
    if "death" in signal.get("summary", "").lower(): conf += 0.05
    return min(1.0, round(conf, 2))

# ═══ Search functions ═══

def get_brave_key():
    try:
        # Try openclaw.json first (standard location)
        for p in ["~/.openclaw/openclaw.json", "~/.openclaw/gateway.json"]:
            cfg_path = os.path.expanduser(p)
            if os.path.exists(cfg_path):
                with open(cfg_path) as f:
                    cfg = json.load(f)
                # Check tools.web.search.apiKey (standard OpenClaw config)
                key = cfg.get("tools", {}).get("web", {}).get("search", {}).get("apiKey", "")
                if key:
                    return key
                # Fallback to legacy locations
                key = cfg.get("braveApiKey", cfg.get("webSearch", {}).get("braveApiKey", ""))
                if key:
                    return key
        return os.environ.get("BRAVE_API_KEY", "")
    except:
        return os.environ.get("BRAVE_API_KEY", "")

def search_web(query, count=8):
    api_key = get_brave_key()
    if not api_key:
        return []
    params = urllib.parse.urlencode({"q": query, "count": str(count), "freshness": "pw"})
    url = "https://api.search.brave.com/res/v1/web/search?" + params
    headers = {"Accept": "application/json", "Accept-Encoding": "gzip", "X-Subscription-Token": api_key}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            try:
                data = json.loads(gzip.decompress(raw))
            except:
                data = json.loads(raw)
        return [{"title": i.get("title",""), "url": i.get("url",""), 
                 "description": i.get("description",""), "published": i.get("age","")}
                for i in data.get("web",{}).get("results",[])]
    except Exception as e:
        print(f"  [!] Search error: {e}", file=sys.stderr)
        return []

def search_bird(query, count=20):
    try:
        result = subprocess.run(
            ["bird", "search", query, "--count", str(count), "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  [!] Bird error: {e}", file=sys.stderr)
    return []

def fetch_who():
    url = "https://www.who.int/api/hubs/diseaseoutbreaknews?$orderby=PublicationDate%20desc&$top=30"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("value", [])
    except Exception as e:
        print(f"  [!] WHO error: {e}", file=sys.stderr)
        return []

def fetch_google_trends():
    """Get Google Trends data for disease + travel keywords."""
    signals = []
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=480)
        
        keyword_sets = [
            ["dengue travel", "malaria travel", "cholera travel"],
            ["sick after travel", "travel illness", "travel outbreak"],
        ]
        
        for keywords in keyword_sets:
            try:
                pytrends.build_payload(keywords, timeframe='now 7-d')
                interest = pytrends.interest_by_region(resolution='COUNTRY')
                
                for kw in keywords:
                    if kw not in interest.columns:
                        continue
                    top = interest[interest[kw] > 50].sort_values(kw, ascending=False).head(5)
                    for country_name, row in top.iterrows():
                        score = int(row[kw])
                        loc = geocode(country_name)
                        if loc:
                            disease_match = detect_diseases(kw)
                            signals.append({
                                "id": make_id(kw + country_name),
                                "source": "trends",
                                "type": "search_spike",
                                "disease": disease_match[0]["name"] if disease_match else kw.split()[0],
                                "category": disease_match[0]["cat"] if disease_match else "unknown",
                                "emoji": disease_match[0]["emoji"] if disease_match else "📈",
                                "location": loc,
                                "severity": min(10, 4 + score // 25),
                                "confidence": 0.50,
                                "summary": "Google Trends: '%s' search interest at %d/100 in %s" % (kw, score, country_name),
                                "url": "https://trends.google.com/trends/explore?q=%s" % urllib.parse.quote(kw),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "published": "last 7 days",
                                "is_traveler": "travel" in kw,
                                "trend_score": score,
                            })
            except Exception as e:
                print(f"  [!] Trends batch error: {e}", file=sys.stderr)
                continue
    except ImportError:
        print("  [!] pytrends not installed", file=sys.stderr)
    except Exception as e:
        print(f"  [!] Trends error: {e}", file=sys.stderr)
    return signals

# ═══ Processing ═══

def process_who(items):
    signals = []
    for item in items:
        title = item.get("Name", item.get("Title", ""))
        desc = item.get("Description", "")[:500]
        text = title + " " + desc
        loc = geocode(text)
        diseases = detect_diseases(text)
        if loc:
            d = diseases[0] if diseases else {"name":"unknown","cat":"unknown","sev":5,"emoji":"🦠"}
            sev = min(10, d["sev"] + (1 if "death" in text.lower() else 0))
            signals.append({
                "id": make_id(title),
                "source": "who",
                "type": "official_alert",
                "disease": d["name"],
                "category": d["cat"],
                "emoji": d["emoji"],
                "location": loc,
                "severity": sev,
                "confidence": 0.95,
                "summary": title[:300],
                "url": "https://www.who.int/emergencies/disease-outbreak-news/item/" + item.get("UrlName", ""),
                "timestamp": item.get("PublicationDate", datetime.now(timezone.utc).isoformat()),
                "published": item.get("PublicationDate", "")[:10],
                "is_traveler": False,
            })
    return signals

def process_news(results, query=""):
    signals = []
    for r in results:
        text = (r.get("title","") + " " + r.get("description","")).strip()
        loc = geocode(text)
        diseases = detect_diseases(text)
        if loc and diseases:
            d = diseases[0]
            sev = min(10, d["sev"] + (1 if "outbreak" in text.lower() else 0) + (1 if "death" in text.lower() else 0))
            traveler = is_traveler_signal(text)
            signals.append({
                "id": make_id(text),
                "source": "news",
                "type": "traveler_report" if traveler else "outbreak_report",
                "disease": d["name"],
                "category": d["cat"],
                "emoji": d["emoji"],
                "location": loc,
                "severity": sev,
                "confidence": 0.75 if traveler else 0.70,
                "summary": text[:300],
                "url": r.get("url", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "published": r.get("published", ""),
                "is_traveler": traveler,
            })
    return signals

def process_tweets(tweets):
    signals = []
    for t in tweets:
        text = t.get("text", t.get("full_text", ""))
        user = t.get("user", {}).get("screen_name", "")
        loc = geocode(text)
        diseases = detect_diseases(text)
        if loc and diseases:
            d = diseases[0]
            traveler = is_traveler_signal(text)
            sev = d["sev"] + (1 if traveler else 0)
            signals.append({
                "id": make_id(text),
                "source": "twitter",
                "type": "traveler_report" if traveler else "symptom_report",
                "disease": d["name"],
                "category": d["cat"],
                "emoji": d["emoji"],
                "location": loc,
                "severity": min(10, sev),
                "confidence": 0.55 if traveler else 0.45,
                "summary": text[:280],
                "url": "https://x.com/%s/status/%s" % (user, t.get("id_str", t.get("id", ""))) if user else "",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "published": t.get("created_at", ""),
                "is_traveler": traveler,
            })
    return signals

def process_reddit(results):
    signals = []
    for r in results:
        text = (r.get("title","") + " " + r.get("description","")).strip()
        loc = geocode(text)
        diseases = detect_diseases(text)
        if loc and (diseases or is_traveler_signal(text)):
            d = diseases[0] if diseases else {"name":"unknown illness","cat":"unknown","sev":4,"emoji":"🌡️"}
            traveler = is_traveler_signal(text)
            signals.append({
                "id": make_id(text),
                "source": "reddit",
                "type": "traveler_report" if traveler else "community_report",
                "disease": d["name"],
                "category": d["cat"],
                "emoji": d["emoji"],
                "location": loc,
                "severity": min(10, d["sev"] + (1 if traveler else 0)),
                "confidence": 0.50 if traveler else 0.40,
                "summary": text[:300],
                "url": r.get("url", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "published": r.get("published", ""),
                "is_traveler": traveler,
            })
    return signals

# ═══ Deduplication ═══
def deduplicate(signals):
    """Remove near-duplicate signals using location+disease clustering."""
    seen = {}
    unique = []
    for s in signals:
        key = (s["location"]["iso"], s["disease"], s["source"])
        if key in seen:
            existing = seen[key]
            if s["severity"] > existing["severity"] or s["confidence"] > existing["confidence"]:
                unique.remove(existing)
                unique.append(s)
                seen[key] = s
        else:
            seen[key] = s
            unique.append(s)
    return unique

# ═══ Anomaly detection ═══
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {"scans": [], "baselines": {}}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def detect_anomalies(signals, history):
    """Compare current signals to historical baseline."""
    baselines = history.get("baselines", {})
    for s in signals:
        key = s["location"]["iso"] + ":" + s["disease"]
        prev_count = baselines.get(key, {}).get("avg_weekly", 0)
        curr_count = sum(1 for x in signals if x["location"]["iso"] == s["location"]["iso"] and x["disease"] == s["disease"])
        
        if prev_count > 0 and curr_count > prev_count * 2:
            s["anomaly"] = True
            s["anomaly_factor"] = round(curr_count / max(prev_count, 0.1), 1)
            s["severity"] = min(10, s["severity"] + 1)
        else:
            s["anomaly"] = curr_count > 0 and prev_count == 0
            s["anomaly_factor"] = None
    
    # Update baselines
    counts = defaultdict(int)
    for s in signals:
        key = s["location"]["iso"] + ":" + s["disease"]
        counts[key] += 1
    
    for key, count in counts.items():
        if key not in baselines:
            baselines[key] = {"avg_weekly": count, "samples": 1}
        else:
            n = baselines[key]["samples"]
            baselines[key]["avg_weekly"] = (baselines[key]["avg_weekly"] * n + count) / (n + 1)
            baselines[key]["samples"] = n + 1
    
    history["baselines"] = baselines
    return signals

# ═══ Flight risk computation ═══
def compute_flight_risk(hotspots):
    """Compute potential spread routes from hotspot countries."""
    routes = []
    for h in hotspots:
        iso = h["iso"]
        if iso in FLIGHT_HUBS:
            for hub in FLIGHT_HUBS[iso]:
                for dest_iata in hub["routes"]:
                    if dest_iata in IATA_COORDS:
                        dest = IATA_COORDS[dest_iata]
                        routes.append({
                            "from": {"lat": hub["lat"], "lng": hub["lng"], "city": hub["city"], "iata": hub["iata"]},
                            "to": {"lat": dest[0], "lng": dest[1], "iata": dest_iata},
                            "threat_level": h["threat_level"],
                            "diseases": h["diseases"],
                            "severity": h["max_severity"],
                        })
    return routes

# ═══ Compute hotspots ═══
def compute_hotspots(signals):
    countries = {}
    for s in signals:
        iso = s["location"]["iso"]
        if iso not in countries:
            countries[iso] = {
                "iso": iso, "name": s["location"]["country"],
                "lat": s["location"]["lat"], "lng": s["location"]["lng"],
                "region": s["location"].get("region", ""),
                "signals": 0, "max_severity": 0,
                "diseases": set(), "sources": set(),
                "has_traveler_signals": False, "has_anomaly": False,
            }
        c = countries[iso]
        c["signals"] += 1
        c["max_severity"] = max(c["max_severity"], s["severity"])
        c["diseases"].add(s["disease"])
        c["sources"].add(s["source"])
        if s.get("is_traveler"): c["has_traveler_signals"] = True
        if s.get("anomaly"): c["has_anomaly"] = True
    
    hotspots = []
    for c in sorted(countries.values(), key=lambda x: -x["max_severity"]):
        threat = "CRITICAL" if c["max_severity"] >= 8 else "HIGH" if c["max_severity"] >= 6 else "MODERATE" if c["max_severity"] >= 4 else "LOW"
        hotspots.append({
            "iso": c["iso"], "name": c["name"],
            "lat": c["lat"], "lng": c["lng"],
            "region": c["region"],
            "signals": c["signals"], "max_severity": c["max_severity"],
            "threat_level": threat,
            "diseases": sorted(c["diseases"]),
            "sources": sorted(c["sources"]),
            "has_traveler_signals": c["has_traveler_signals"],
            "has_anomaly": c["has_anomaly"],
        })
    return hotspots

# ═══ Main scan ═══
def run_scan():
    import time
    t0 = time.time()
    
    print("=" * 60)
    print("🛰️  GeoSentinel 2.0 Scanner v2 — Full Spectrum Scan")
    print("=" * 60)
    
    all_signals = []
    
    # 1. WHO
    print("\n📡 [1/5] WHO Disease Outbreak News...")
    who = fetch_who()
    print(f"   → {len(who)} items")
    all_signals.extend(process_who(who))
    
    # 2. News (Brave)
    news_queries = [
        "disease outbreak 2026 travel",
        "dengue outbreak cases 2026",
        "cholera outbreak 2026",
        "malaria outbreak surge 2026",
        "avian flu H5N1 outbreak 2026",
        "measles outbreak cases 2026",
        "mpox cases outbreak 2026",
        "travelers sick returning illness",
        "travel health warning disease",
        "ebola marburg outbreak Africa 2026",
        "typhoid outbreak travel",
        "meningitis outbreak 2026",
        "nipah virus outbreak",
        "yellow fever outbreak 2026",
        "lassa fever outbreak",
        "polio cases outbreak",
    ]
    print(f"\n🔍 [2/5] News search ({len(news_queries)} queries)...")
    for i, q in enumerate(news_queries):
        results = search_web(q, count=5)
        sigs = process_news(results, q)
        if sigs:
            print(f"   [{i+1}/{len(news_queries)}] '{q}' → {len(sigs)} signals")
        all_signals.extend(sigs)
        time.sleep(1.1)  # rate limit
    
    # 3. Twitter
    twitter_queries = [
        "sick after traveling fever",
        "got malaria travel Africa",
        "dengue travel sick hospital",
        "food poisoning travel diarrhea",
        "outbreak warning travel alert",
        "came back sick from trip",
        "travel illness hospitalized",
        "cholera outbreak travel warning",
        "tourist sick hospital tropical",
        "traveler quarantine infection",
    ]
    print(f"\n🐦 [3/5] Twitter/X ({len(twitter_queries)} queries)...")
    for q in twitter_queries:
        tweets = search_bird(q, count=15)
        sigs = process_tweets(tweets)
        if sigs:
            print(f"   '{q}' → {len(sigs)} signals")
        all_signals.extend(sigs)
    
    # 4. Reddit (via web search)
    reddit_queries = [
        "site:reddit.com travel sick illness trip",
        "site:reddit.com got dengue traveling",
        "site:reddit.com malaria travel experience",
        "site:reddit.com food poisoning travel country",
        "site:reddit.com travel health warning outbreak",
        "site:reddit.com sick after vacation tropical",
    ]
    print(f"\n💬 [4/5] Reddit ({len(reddit_queries)} queries)...")
    for q in reddit_queries:
        results = search_web(q, count=5)
        sigs = process_reddit(results)
        if sigs:
            print(f"   '{q}' → {len(sigs)} signals")
        all_signals.extend(sigs)
        time.sleep(1.1)
    
    # 5. Google Trends
    print("\n📈 [5/5] Google Trends...")
    trend_signals = fetch_google_trends()
    print(f"   → {len(trend_signals)} signals")
    all_signals.extend(trend_signals)
    
    # Post-processing
    print("\n⚙️  Processing...")
    
    # Compute confidence
    for s in all_signals:
        s["confidence"] = compute_confidence(s)
    
    # Deduplicate
    before = len(all_signals)
    all_signals = deduplicate(all_signals)
    print(f"   Dedup: {before} → {len(all_signals)}")
    
    # Sort by severity × confidence
    all_signals.sort(key=lambda x: -(x["severity"] * x["confidence"]))
    
    # Anomaly detection
    history = load_history()
    all_signals = detect_anomalies(all_signals, history)
    anomalies = sum(1 for s in all_signals if s.get("anomaly"))
    print(f"   Anomalies: {anomalies}")
    
    # Hotspots
    hotspots = compute_hotspots(all_signals)
    
    # Flight risk routes
    flight_routes = compute_flight_risk(hotspots)
    print(f"   Flight risk routes: {len(flight_routes)}")
    
    # Stats
    traveler_count = sum(1 for s in all_signals if s.get("is_traveler"))
    stats = {
        "total_signals": len(all_signals),
        "by_source": {},
        "by_category": {},
        "by_severity": {"critical": 0, "high": 0, "moderate": 0, "low": 0},
        "by_region": {},
        "by_type": {},
        "countries_affected": len(hotspots),
        "traveler_signals": traveler_count,
        "anomalies_detected": anomalies,
        "scan_duration_sec": round(time.time() - t0, 1),
    }
    for s in all_signals:
        stats["by_source"][s["source"]] = stats["by_source"].get(s["source"], 0) + 1
        stats["by_category"][s["category"]] = stats["by_category"].get(s["category"], 0) + 1
        stats["by_type"][s["type"]] = stats["by_type"].get(s["type"], 0) + 1
        r = s["location"].get("region", "Unknown")
        stats["by_region"][r] = stats["by_region"].get(r, 0) + 1
        if s["severity"] >= 8: stats["by_severity"]["critical"] += 1
        elif s["severity"] >= 6: stats["by_severity"]["high"] += 1
        elif s["severity"] >= 4: stats["by_severity"]["moderate"] += 1
        else: stats["by_severity"]["low"] += 1
    
    # Save
    output = {
        "version": "2.0",
        "lastScan": datetime.now(timezone.utc).isoformat(),
        "scanDuration": stats["scan_duration_sec"],
        "signals": all_signals,
        "hotspots": hotspots,
        "flightRoutes": flight_routes,
        "stats": stats,
    }
    
    os.makedirs(os.path.dirname(SIGNALS_FILE), exist_ok=True)
    with open(SIGNALS_FILE, "w") as f:
        json.dump(output, f, indent=2)
    
    # Update history
    history["scans"].append({"time": output["lastScan"], "signals": len(all_signals), "hotspots": len(hotspots)})
    history["scans"] = history["scans"][-30:]  # keep last 30
    save_history(history)
    
    elapsed = round(time.time() - t0, 1)
    print(f"\n{'=' * 60}")
    print(f"✅ Scan complete in {elapsed}s")
    print(f"   📊 {len(all_signals)} signals | {len(hotspots)} hotspots | {len(flight_routes)} flight routes")
    print(f"   🔴 Critical: {stats['by_severity']['critical']} | 🟠 High: {stats['by_severity']['high']} | 🟡 Moderate: {stats['by_severity']['moderate']} | 🟢 Low: {stats['by_severity']['low']}")
    print(f"   ✈️  Traveler signals: {traveler_count} | ⚠️  Anomalies: {anomalies}")
    print(f"   Sources: {', '.join(stats['by_source'].keys())}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    run_scan()
