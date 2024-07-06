# Scrape Sites for Doctor Contact Information
#
# Site Links:
# https://www.a4m.com/, https://www.aanp.org/, https://naturopathic.org/, https://www.aznma.org/, https://biote.com/
# Each Doctor Should be represented as a JSON Object with at least a name, state, full address, and phone number

import requests
import json
from os.path import exists
from pprint import pprint

def datacache(scrapefunction):
    datafilename = f'scrapecache/{scrapefunction.__name__.replace("scrape_", "")}.json'
    if exists(datafilename):
        datafile = open(datafilename, "r")
        print(f"Using cached scrape data for {scrapefunction.__name__.replace('scrape_', '')}")
        return json.load(datafile)
    data = scrapefunction()
    with open(datafilename, "w") as datafile:
        json.dump(data, datafile)
    return data

@datacache
def scrape_a4m() -> dict[str, dict[str, str]]:
    print("Scraping Doctor Information from a4m")
    a4m_aggregated_data = {}
    doctor_metadata = json.loads(requests.get("""https://www.a4m.com/listing-search/coordinates?listing_type[]=fd6334c22b25d2dbd8b4f0ab910395fd&listing_type[]=d8eab40b3150f7b3f26af1e68513c924&keyword=&location=&radius=24000&doctor=yes&alphaCol=fname|lname&lat=35&lng=-100""").text)["message"]
    doctornum = 1
    for doctor in doctor_metadata:
        doctor_info = json.loads(requests.get(f"https://www.a4m.com/listing-search/listings?id[]={doctor['id']}").text)['message'][0]
        if doctor_info['country'] != 'United States':
            continue
        doctor_name = doctor["sortAlpha"]
        a4m_aggregated_data[doctor_name] = {}
        a4m_aggregated_data[doctor_name]['degrees'] = doctor_info['degrees']
        a4m_aggregated_data[doctor_name]['phone'] = doctor_info['phone']
        a4m_aggregated_data[doctor_name]['state'] = doctor_info['state']
        a4m_aggregated_data[doctor_name]['address'] = (f"{doctor_info['address1']}, " if doctor_info['address1'] else "") + f"{doctor_info['city']}, {doctor_info['state']}, {doctor_info['zip']}"
        a4m_aggregated_data[doctor_name]['url'] = doctor_info['url']
        doctornum += 1
    print(f"Scraped {doctornum} contacts from a4m.")
    return a4m_aggregated_data

@datacache
def scrape_aanp():
    doctornum = 0
    aanp_aggregated_data = {}
    print("Scraping Doctor Information From AANP")
    for long in range(-125 * 2, -64 * 2):
        for lat in range(25, 51):
            if lat == 50:
                print(f"Reached lat {lat} and long {long / 2}")
            query_json = {
                "query": {
                    "Center": {
                        "Latitude": lat,
                        "Longitude": long / 2
                    },
                    "Radius": 100
                }
            }
            doctor_metadata = json.loads(requests.post("https://my.aanp.org/WebServices/FinderService__c.asmx/Search", json=query_json).text)
            doctor_information = json.loads(doctor_metadata['d'])
            for doctor_metadata in doctor_information:
                doctor_name = f'{doctor_metadata["ContactDataIndividualFirstName"]} {doctor_metadata["ContactDataIndividualLastName"]}'.title()
                if doctor_name in aanp_aggregated_data.keys():
                    continue
                aanp_aggregated_data[doctor_name] = {}
                aanp_aggregated_data[doctor_name]["phone"] = doctor_metadata['Phone']
                aanp_aggregated_data[doctor_name]['state'] = doctor_metadata['AddressState']
                aanp_aggregated_data[doctor_name]['company'] = doctor_metadata['CompanyName'].title()
                aanp_aggregated_data[doctor_name]['address'] = f"{doctor_metadata['AddressStreet1']}, {doctor_metadata['AddressCity']}, {doctor_metadata['AddressState']}, {doctor_metadata['AddressPostalCode'][:5]}"
                aanp_aggregated_data[doctor_name]['url'] = doctor_metadata['Website'] if 'Website' in doctor_metadata.keys() else ""
                doctornum += 1
    print(f"Scraped {doctornum} contacts from a4m.")
    return aanp_aggregated_data

def scrape_naturopathic():
    doctornum = 0
    naturopathic_aggregated_data = {}
    print("Scraping Contact Information from Naturopathic")

def main():
    a4m_data = scrape_a4m
    aanp_data = scrape_aanp
    with open("sources.csv", "a", encoding='utf8') as outputfile:
        outputfile.write("Source Name, Degrees, Phone Number, State, Company, Address, URL, Dataset\n")
        for name, data in a4m_data.items():
            outputfile.write(f"{convertCSVString(name)}, {convertCSVString(data['degrees'])}, {convertCSVString(data['phone'])}, {convertCSVString(data['state'])}, N/A, {convertCSVString(data['address'])}, {convertCSVString(data['url'])}, a4m\n")
        for name, data in aanp_data.items():
            outputfile.write(f"{convertCSVString(name)}, N/A, {convertCSVString(data['phone'])}, {convertCSVString(data['state'])}, {convertCSVString(data['company'])}, {convertCSVString(data['address'])}, {convertCSVString(data['url'])}, AANP\n")
    print(f"Size of Contact Dataset: {len(scrape_aanp.keys()) + len(scrape_a4m.keys())}")

def convertCSVString(input):
    if not input:
        return ""
    return input.replace(',', ';')

if __name__ == '__main__':
    main()
