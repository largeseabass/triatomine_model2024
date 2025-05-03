import pandas as pd
from geopy.geocoders import Nominatim
import numpy as np
import difflib
from translate import Translator
from unidecode import unidecode
import multiprocessing 
import pycountry
import warnings
import time


"""
ingredients to use
"""

species_feature_list = np.array(['id',
    'Genus', 
    'Species', 
    'Subspecies',
    'Sex', 
    'Habitat',
    'Collection Method',
    'count',
    'Natural infection information',
    'observation comment',
    'num_identification_agreements',
    'num_identification_disagreements',
    #geographical info
    'Location',
    'MunicipioCounty', 
    'StateProvince',
    'Country', 
    'DecimalLatitude', 
    'DecimalLongitude', 
    'Altitude MASL',
    'georeferenceSources',
    'positional_accuracy',
    'public_positional_accuracy',                        
    'geoprivacy',
    'Comments on coordinates', 
    #time
    'year-begin',
    'month-begin',
    'day-begin',
    'year-end',
    'month-end',
    'day-end',
    'time',
    'time zone',
    'time notes',
    'time comment',
    #collector information
    'Primary Collector info',
    'Secondary Collector info',
    #quality control
    'data quality',
    'duplication',
    'coordinate reliability',
    'on the land',
    'select for 2023 model'])



"""
versatile cleaning functions
"""




def check_georef(df_this,decimalLatitude,decimalLongitude, country, stateProvince,municipality, locality, this_ind,user_agent):
# Check if their coordinates indicate the same county, state, country information as the corresponding record.
# the translation relies on google translator. It does not always work. Therefore, this function returns -1 as a flag for successfully run through all the rows in the dataframe df_this     
# df_this (pd.dataframe), the pandas dataframe storing all the data
# decimalLatitude (float), the name (string) of the column that stores the decimalLatitude (float)
# decimalLongitude (float), the name (string) of the column that stores the decimalLongitude (float)
# country (string), the name (string) of the column that stores the country name (string)
# stateProvince (string), the name (string) of the column that stores the state or province name (string)
# municipality (string), the name (string) of the column that stores the municipality name (string)
# locality (string), the name (string) of the column that stores the locality name (string)
# this_ind (int), if for some reasons, the georef check function doesn't run till the last row in the last run, input the index (int) of the row that causes the problem, and this time we start from that row.
# user_agent (string): used for calling google translator, I used my email here
    warnings.filterwarnings("ignore")

    for ind in df_this.index:
        geolocator = Nominatim(user_agent=user_agent+":"+str(ind))
        
        if not np.isnan(this_ind):
            if ind < this_ind:
                continue

        if np.isnan(df_this[decimalLatitude][ind]):
            All_the_same = False
            same_municipality = False
            same_state = False
            same_country = False
            print("no coordinates")
            df_this["coordinate reliability"][ind] = "no coordinates"
            continue

        else:
            try:
                location = geolocator.reverse(str(df_this[decimalLatitude][ind])+","+str(df_this[decimalLongitude][ind]),language="en")

                address = location.raw['address']
            except AttributeError:
                df_this["coordinate reliability"][ind] = "not on land"
                continue
            except:
                print("something wrong!")
                print(ind)
                print(df_this[decimalLatitude][ind])
                print(df_this[decimalLongitude][ind])
                return ind




            key_list=np.array(list(address.keys()))


            state_where = np.where(key_list == 'state')[0]


            this_country = address.get('country', '')
            this_state = address.get('state', '')
            record_country = str(df_this[country][ind])
            record_state = str(df_this[stateProvince][ind])
            record_municipality = str(df_this[municipality][ind])
            record_locality = str(df_this[locality][ind])
#             print('country'+str(record_country)+', state:'+str(record_state) +', municipality:'+str(record_municipality)+', locality:'+str(record_locality))
            

#             print(type(record_locality))


            All_the_same = False
            same_municipality = False
            same_state = False
            same_country = False
            translate_M = False

            try:
                if not pd.isnull(record_country):
                    if record_country == this_country:
                        same_country = True 
                    elif unidecode(address.get('country', '')).strip() == unidecode(this_country).strip():
                        same_country = True
            except RuntimeError:
                print('Run Time Error - translate country - '+address.get(this_key, ''))

            if same_country:
                if not pd.isnull(record_state):
                    if (record_state in this_state) or (this_state in record_state):
                        same_state = True
                    else:
                        try:
                            this_state = unidecode(this_state)
                            record_state = unidecode(record_state)
                        except RuntimeError:
                            print('Run Time Error - translate state - '+address.get(this_key, ''))
                        if (record_state in this_state) or (this_state in record_state):
                            same_state = True
            # iterate over all the 'smaller' keys. decide if the finest location is recorded correctly.
            if same_state:
                if not pd.isnull(record_municipality):
                    count_num = state_where - 1
                    while count_num >= 0:
                        this_key = key_list[count_num][0]
                        this_item = address.get(this_key, '')
                        #print(type(this_item))
                        if same_municipality:
                            if (record_locality in this_item) or (this_item in record_locality):
                                All_the_same = True
                            else:
                                try:
                                    this_item = unidecode(this_item)
                                    record_locality = unidecode(record_locality)
                                except RuntimeError:
                                    print('Run Time Error - translate locality - '+address.get(this_key, ''))

                                if (record_locality in this_item) or (this_item in record_locality):
                                    All_the_same = True

                        else:# see if same municipality
                            if (record_municipality in this_item) or (this_item in record_municipality):
                                same_municipality = True
                            else:
                                try:
                                    if not translate_M:
                                        record_municipality = unidecode(record_municipality)
                                        translate_M = True
                                    this_item = unidecode(this_item)
                                except RuntimeError:
                                    print('Run Time Error - translate municipality - '+address.get(this_key, ''))

                                if (record_municipality in this_item) or (this_item in record_municipality):
                                    same_municipality = True
                                    if pd.isnull(record_locality):
                                        break

                        count_num = count_num - 1


        if same_country:
            if same_state:
                if same_municipality:
                    if All_the_same:
                        #print("all agree")
                        df_this["coordinate reliability"][ind] = "all agree"
                    else:
                        #print("Location different")
                        df_this["coordinate reliability"][ind] = "Location different"
                else:
                    #print("MunicipioCounty different")
                    df_this["coordinate reliability"][ind] = "MunicipioCounty different"

            else:
                #print("StateProvince different")
                df_this["coordinate reliability"][ind] = "StateProvince different"
        else:
            #print("Country different")
            df_this["coordinate reliability"][ind] = "Country different"
    
    return -1




# Check for duplication of record

def check_dup(df_this):
    this_length = len(df_this['DecimalLatitude'])
    for ind in df_this.index:
        #print(df_this['duplication'][ind])
        #print(type(df_this['duplication'][ind]))
        if not pd.isnull(df_this['duplication'][ind]):
            continue
        if pd.isnull(df_this['DecimalLatitude'][ind]):
            continue
        if pd.isnull(df_this['year-begin'][ind]):
            continue
        
        this_lat = np.ones(this_length)*df_this['DecimalLatitude'][ind]
        this_lon = np.ones(this_length)*df_this['DecimalLongitude'][ind]
        this_year = np.ones(this_length)*df_this['year-begin'][ind]
        all_other_lat = np.array(df_this['DecimalLatitude'])
        all_other_lon = np.array(df_this['DecimalLongitude'])
        all_other_year = np.array(df_this['year-begin'])
        
        diff_distance = np.absolute(np.square(this_lat-all_other_lat)+np.square(this_lon-all_other_lon))
        diff_year = np.absolute(np.square(this_year-all_other_year))
        index_suspect = np.intersect1d(np.where( diff_distance < 0.05),np.where(diff_year < 1))
        #print(index_suspect)
        
        this_species = df_this['Species'][ind]
        
        for this_index in index_suspect:
            if this_index == ind:
                continue
            if this_species == df_this['Species'][ind]:
                df_this['duplication'][ind]= index_suspect
                #print('duplicate warning')
        
            


# unique cleaning function for each dataset

# new collect

def pre_process_df_new_collect(raw_csv_path,my_email,csv_saving_path):
    csv_path0 = raw_csv_path
    df_species_0 = pd.read_csv(csv_path0)
    df_species_state = np.nan
    while df_species_state!= -1:
        df_species_state = check_georef(df_species_0,'DecimalLatitude','DecimalLongitude', 'Country', 'StateProvince','MunicipioCounty', 'Location',df_species_state,my_email)
        time.sleep(1)
    df_species_0.to_csv(csv_saving_path)
    print("success")
                
# new mexico 
def new_mexico_roman_integer(roman_l):
    
    if roman_l == "I":
        return 1
    if roman_l == "II":
        return 2
    if roman_l == "III":
        return 3
    if roman_l == "IV":
        return 4
    if roman_l == "V":
        return 5
    if roman_l == "VI":
        return 6
    if roman_l == "VII":
        return 7
    if roman_l == "VIII":
        return 8
    if roman_l == "IX":
        return 9
    if roman_l == "X":
        return 10
    if roman_l == "XI":
        return 11
    if roman_l == "XII":
        return 12
    
    return np.nan


def new_mexico_time(df_this,time_feature):
    warnings.filterwarnings("ignore")
    for ind in df_this.index:
        this_text = df_this[time_feature][ind]
        #print(this_text)
        if pd.isnull(this_text):
            #print('null')
            continue
        if this_text!='NE':
            if not ("-" in this_text):
                continue
            if "a" in this_text:
                split_list = this_text.split("a")
            else:
                if "A" in this_text:
                    split_list = this_text.split("A")
                else:
                    continue
            
        if 'y' in split_list[0]:
            # before
            remove_y = split_list[0].split("y")
            before_split = remove_y[0].split("-")
            if len(before_split) == 3:
                #something
                before_day = int(before_split[0].strip())
                before_month = new_mexico_roman_integer(before_split[1].strip())
                before_year = int(before_split[2].strip())
                #print(str(before_day)+' '+str(before_month)+' '+str(before_year))
                df_this['year-begin'][ind] = before_year
                df_this['month-begin'][ind] = before_month
                df_this['day-begin'][ind] = before_day

            else:
                #equals 2
                before_month = new_mexico_roman_integer(before_split[0].strip())
                before_year = int(before_split[1].strip())
                #print(str(before_month)+' '+str(before_year))
                df_this['year-begin'][ind] = before_year
                df_this['month-begin'][ind] = before_month

        else:
            # before
            before_split = split_list[0].split("-")
            if len(before_split) == 3:
                #something
                before_day = int(before_split[0].strip())
                before_month = new_mexico_roman_integer(before_split[1].strip())
                before_year = int(before_split[2].strip())
                #print(str(before_day)+' '+str(before_month)+' '+str(before_year))
                df_this['year-begin'][ind] = before_year
                df_this['month-begin'][ind] = before_month
                df_this['day-begin'][ind] = before_day
                
            else:
                #equals 2
                before_month = new_mexico_roman_integer(before_split[0].strip())
                before_year = int(before_split[1].strip())
                #print(str(before_month)+' '+str(before_year))
                df_this['year-begin'][ind] = before_year
                df_this['month-begin'][ind] = before_month

        # after
        after_split = split_list[1].split("-")
        if len(after_split) == 3:
            #something
            after_day = int(after_split[0].strip())
            after_month = new_mexico_roman_integer(after_split[1].strip())
            after_year = int(after_split[2].strip())
            #print(str(after_day)+' '+str(after_month)+' '+str(after_year))
            df_this['year-end'][ind] = after_year
            df_this['month-end'][ind] = after_month
            df_this['day-end'][ind] = after_day

        else:
            #equals 2
            after_month = new_mexico_roman_integer(after_split[0].strip())
            after_year = int(after_split[1].strip())
            #print(str(after_month)+' '+str(after_year))
            df_this['year-end'][ind] = after_year
            df_this['month-end'][ind] = after_month

        #print(split_list)
             

def pre_process_df_update_mexico(raw_csv_path,my_email,csv_saving_path):
    # raw_csv_path (string): path to the raw csv file
    # my_email (string): the email address fed to google translator for georef checking
    # csv_saving_path (string): path to save the processed csv file

    csv_path3 = raw_csv_path
    df_test3 = pd.read_csv(csv_path3)
    df_species_3 = pd.DataFrame(columns=species_feature_list)
    df_species_3['Genus'] = df_test3[['Género (Genus)']].copy()
    df_species_3['Species'] = df_test3[['especie (species)']].copy()
    df_species_3['Subspecies'] = df_test3[['subespecie (subspecies)']].copy()
    df_species_3['Sex'] = df_test3[['Sexo (Sex)']].copy()
    df_species_3['Habitat'] = df_test3[['Hábitat (Habitat)']].copy()
    df_species_3['Collection Method'] = df_test3[['tipo de recolección (type of collection)']].copy()
    df_species_3['Natural infection information'] = df_test3[['Información sobre Infección natural (info on natural infection)']].copy()
    df_species_3['observation comment'] = df_test3[['Comentarios generales (general comments)']].copy()
    df_species_3['Location'] = df_test3[['Localidad exacta (Exact locality)']].copy()
    df_species_3['MunicipioCounty'] = df_test3[['Municipio (County)']].copy()
    df_species_3['StateProvince'] = df_test3[['Estado (State)']].copy()
    df_species_3['Country'] = df_test3[['País (Country)']].copy()
    df_species_3['DecimalLatitude'] = df_test3[['Latitude (Decimal Degrees)']].copy()
    df_species_3['DecimalLongitude'] = df_test3[['Longitude (Decimal Degrees)']].copy()
    df_species_3['Comments on coordinates'] = df_test3[['Comments on coordinates']].copy()
    df_species_3['Altitude MASL'] = df_test3[['Altitud msnm (Altitude masl)']].copy()
    df_species_3['time notes'] = df_test3[['Fecha de colecta (día -  mes - año) (si se conoce) (Collection date - day-month-year)']].copy()
    df_species_3['time comment'] = np.where('(considering date of publication)' in df_test3['Year of collection (range approximately)'], 'considering date of publication',np.nan)
    df_species_3['Primary Collector info'] = df_test3[[' Information source (Source of information)']].copy()
    df_species_3['Secondary Collector info'] = df_test3[['Información recopilada por (Information gathered by)']].copy()
    df_species_3['data quality'] = df_test3[['Locality Scale']].copy()


    new_mexico_time(df_species_3,'time notes')
    df_species_3 = df_species_3.replace('NE', np.nan)


    df_species_state = np.nan
    while df_species_state!= -1:
        df_species_state = check_georef(df_species_3,'DecimalLatitude','DecimalLongitude', 'Country', 'StateProvince','MunicipioCounty', 'Location',df_species_state,my_email)
        time.sleep(1)
    df_species_3.to_csv(csv_saving_path)
    print("success")






# 2018 nature
def year_for_2018(df_this,df_ref):
    for ind in df_ref.index:
        
        #sort out the year 
        
        this_year = df_ref['year'][ind]
        
        if pd.isnull(this_year):
            continue
        #print(this_year)
        if '-' in this_year:
            before_split = this_year.split("-")
            df_this['year-begin'][ind]=int(before_split[0].strip())

            if '[' in before_split[-1]:
                df_this['year-end'][ind]=int(before_split[-1].split('[')[0].strip())
            else:
                df_this['year-end'][ind]=int(before_split[-1].strip())

        else:
            if '–' in this_year:
                before_split = this_year.split("–")
                df_this['year-begin'][ind]=int(before_split[0].strip())
                df_this['year-end'][ind]=int(before_split[-1].strip())
                continue
            if ';' in this_year:
                before_split = this_year.split(";")
                df_this['year-begin'][ind] = int(before_split[0].strip())
                df_this['year-end'][ind] = int(before_split[-1].strip())
                continue
            
            if len(this_year) == 4 and this_year.isdigit():
                df_this['year-begin'][ind] = int(this_year)
                continue
            
            if 'until' in this_year:
                df_this['year-end'][ind] = int(this_year[-4:])
                continue
                
            print("no: "+ this_year)
            print(type(this_year))
        
def month_digit_2018(month):
    if month == "january":
        return 1
    if month == "february":
        return 2
    if month == "march":
        return 3
    if month == "april":
        return 4
    if month == "may":
        return 5
    if month == "june":
        return 6
    if month == "july":
        return 7
    if month == "august":
        return 8
    if month == "september":
        return 9
    if month == "october":
        return 10
    if month == "november":
        return 11
    if month == "december":
        return 12
    
    return np.nan
    
def month_for_2018(df_this,df_ref):
     for ind in df_ref.index:
        
        #sort out the year 
        
        this_month = df_ref['month'][ind]
        if pd.isnull(this_month):
            continue
        
        if '&' in this_month:
            
            if '|' in this_month:
                
                before_split = this_month.split("|")
                
                if '-' in before_split[0]:
                    this_split = before_split[0].split("-")
                    df_this['month-begin'][ind] =month_digit_2018(this_split[0])
                    
                if '&' in before_split[0]:
                    this_split = before_split[0].split("&")
                    df_this['month-begin'][ind] =month_digit_2018(this_split[0])
                

                this_after_item = before_split[1]
                if '&' in this_after_item:
                    this_after_item = this_after_item.split("&")[-1]
                if '(' in this_after_item:
                    this_after_item = this_after_item.split("(")[-2]
                
                df_this['month-end'][ind] =month_digit_2018(this_after_item)

            continue
        
        
        if '|' in this_month:
            before_split = this_month.split("|")

            if '(' in before_split[0]:
                this_one = before_split[0].split("(")[0]
                df_this['month-begin'][ind] = month_digit_2018(this_one)
                
            else:
                print('no!!!'+before_split[0])
            
            if '(' in before_split[1]:
                this_one = before_split[1].split("(")[0]
                df_this['month-end'][ind] = month_digit_2018(this_one)
                
            else:
                if '1' in before_split[1]:
                    this_one = before_split[1].split("1")[0]
                    df_this['month-end'][ind] = month_digit_2018(this_one)
                    
                else:
                    print('no!!!'+before_split[1])

            continue
            
        if '-' in this_month:
            before_split = this_month.split("-")
            df_this['month-begin'][ind] = month_digit_2018(before_split[0])
            df_this['month-end'][ind] = month_digit_2018(before_split[1])
            continue
        
        digit_it = month_digit_2018(this_month.lower())
        
        if '(' in this_month:
            before_split = this_month.split("(")
            df_this['month-begin'][ind] = month_digit_2018(before_split[0])
            continue
        
        digit_it = month_digit_2018(this_month.lower())
        
        if np.isnan(digit_it):
            print('bad value'+this_month)
        else:
            df_this['month-begin'][ind] = digit_it
            continue

def day_for_2018(df_this,df_ref):
    for ind in df_ref.index:
        
        #sort out the year 
        
        this_day = df_ref['day'][ind]
        if pd.isnull(this_day):
            continue
        if this_day.isdigit():
            if int(this_day) > 0 and int(this_day)<32:
                continue
                df_this['day-begin'][ind] = int(this_day)
            continue
        
        if '-' in this_day:
            if 'to' in this_day:
                df_this['day-begin'][ind] = int(this_day[0:1])
                df_this['day-end'][ind] = int(this_day[-2:-1])
                continue
            
            before_split = this_day.split("-")
            if before_split[0].isdigit():
                df_this['day-begin'][ind] =int(before_split[0])
                df_this['day-end'][ind] =int(before_split[-1])
                continue

            if this_day[0].isdigit():
                before_split = this_day.split("-")
                before_split1 = before_split[0].split("/")
                before_split2 = before_split[1].split("/")
                df_this['day-begin'][ind] =int(before_split1[0])
                df_this['day-end'][ind] = int(before_split2[0])
                continue
            #print(this_day)
            continue
        if 'to' in this_day:
            before_split = this_day.split("to")
            before_split1 = before_split[0].split("/")
            before_split2 = before_split[1].split("/")
            df_this['day-begin'][ind] =int(before_split1[0])
            df_this['day-end'][ind] = int(before_split2[0])
            continue
        
def pre_process_df_2018_nature(raw_csv_path,my_email,csv_saving_path):
    # raw_csv_path (string): path to the raw csv file
    # my_email (string): the email address fed to google translator for georef checking
    # csv_saving_path (string): path to save the processed csv file
    df_test1 = pd.read_csv(raw_csv_path)
    # For 2018
    df_species_1 = pd.DataFrame(columns=species_feature_list)
    df_species_1[['Genus', 'Species']] = df_test1['scientificName'].str.split(pat = ' ', expand = True)

    df_species_1['Habitat'] = df_test1[['habitat']].copy()
    df_species_1['Collection Method'] = df_test1[['samplingProtocol']].copy()
    df_species_1['count'] = df_test1[['individualCount']].copy()

    df_species_1['Location'] = df_test1[['locality']].copy()
    df_species_1['MunicipioCounty'] = df_test1[['municipality']].copy()
    df_species_1['StateProvince'] = df_test1[['stateProvince']].copy()
    df_species_1['Country'] = df_test1[['country']].copy()
    df_species_1['DecimalLatitude'] = df_test1[['decimalLatitude']].copy()
    df_species_1['DecimalLongitude'] = df_test1[['decimalLongitude']].copy()
    df_species_1['georeferenceSources'] = df_test1[['georeferenceSources']].copy()
    # df_species_3['time notes'] = df_test3[['Fecha de colecta (día -  mes - año) (si se conoce) (Collection date - day-month-year)']].copy()
    # df_species_3['time comment'] = np.where('(considering date of publication)' in df_test3['Year of collection (range approximately)'], 'considering date of publication',np.nan)
    df_species_1['Primary Collector info'] = df_test1[['associatedReferences']].copy()
    df_species_1['Secondary Collector info'] = 'Ceccarelli, S., Balsalobre, A., Medone, P. et al. DataTri, a database of American triatomine species occurrence. Sci Data 5, 180071 (2018). https://doi.org/10.1038/sdata.2018.71'

    # call the function to sort out times
    year_for_2018(df_species_1,df_test1)
    month_for_2018(df_species_1,df_test1)
    day_for_2018(df_species_1,df_test1)
    #georef
    df_species_state = np.nan
    while df_species_state!= -1:
        df_species_state = check_georef(df_species_1,'DecimalLatitude','DecimalLongitude', 'Country', 'StateProvince','MunicipioCounty', 'Location',df_species_state,my_email)
        time.sleep(1)
    df_species_1.to_csv(csv_saving_path)
    print("success")


# inaturalist 


def pre_process_df_inaturalist(raw_csv_path,my_email,csv_saving_path):
    # raw_csv_path (string): path to the raw csv file
    # my_email (string): the email address fed to google translator for georef checking
    # csv_saving_path (string): path to save the processed csv file
    # modified complete!

    df_test2 = pd.read_csv(raw_csv_path)
    df_species_2 = pd.DataFrame(columns=species_feature_list)
    df_species_2['Genus']=df_test2['genus'].copy()
    df_species_2['Species']=df_test2['specificEpithet'].copy()
    #df_species_2[['Genus', 'Species']] = df_test2['taxon_species_name'].str.split(pat = ' ', expand = True)

    df_species_2['observation comment'] = df_test2['lifeStage'].copy()
    df_species_2['Habitat'] = df_test2['occurrenceRemarks'].copy()

    df_species_2['Collection Method'] = 'Citizen science observation'
    df_species_2['Sex'] = df_test2['sex'].copy()


    # df_species_2['num_identification_agreements'] = df_test2[['num_identification_agreements']].copy()#?
    # df_species_2['num_identification_disagreements'] = df_test2[['num_identification_disagreements']].copy()#?


    df_species_2['Location'] = df_test2[['level3Name']].copy()
    df_species_2['MunicipioCounty'] = df_test2[['level2Name']].copy()
    df_species_2['StateProvince'] = df_test2[['level1Name']].copy()
    df_species_2['Country'] = df_test2['level0Name'].copy()
    df_species_2['Comments on coordinates'] = df_test2['verbatimLocality'].copy()

    df_species_2['DecimalLatitude'] = df_test2[['decimalLatitude']].copy()
    df_species_2['DecimalLongitude'] = df_test2[['decimalLongitude']].copy()

    df_species_2['positional_accuracy'] = df_test2['coordinateUncertaintyInMeters'].copy()

    #df_species_2[['year-begin','month-begin','day-begin']] = df_test2['observed_on'].str.split(pat = '-', expand = True).astype(int)
    df_species_2['year-begin'] = df_test2['year'].copy()
    df_species_2['month-begin'] = df_test2['month'].copy()
    df_species_2['day-begin'] = df_test2['day'].copy()
    df_species_2['time'] = df_test2[['eventTime']].copy()


    # # df_species_3['time notes'] = df_test3[['Fecha de colecta (día -  mes - año) (si se conoce) (Collection date - day-month-year)']].copy()
    # # df_species_3['time comment'] = np.where('(considering date of publication)' in df_test3['Year of collection (range approximately)'], 'considering date of publication',np.nan)
    df_species_2['Primary Collector info'] = 'recorded by: '+df_test2['recordedBy']+', identified by: '+df_test2['identifiedBy']+', '+df_test2['identifiedByID']+', comments: '+df_test2['identificationRemarks'].copy()
    df_species_2['Secondary Collector info'] = 'iNaturalist research-grade observations'
    df_species_2['data quality'] = df_test2[['issue']].copy()

    df_species_state = np.nan
    while df_species_state!= -1:
        df_species_state = check_georef(df_species_2,'DecimalLatitude','DecimalLongitude', 'Country', 'StateProvince','MunicipioCounty', 'Location',df_species_state,my_email)
    df_species_2.to_csv(csv_saving_path)
    print("success")


# stavana's dataset




def check_georef_stavana(df_this,decimalLatitude,decimalLongitude, country, stateProvince,municipality, locality, this_ind,user_agent):
# Check if their coordinates indicate the same county, state, country information as the corresponding record.
# the translation relies on google translator. It does not always work. Therefore, this function returns -1 as a flag for successfully run through all the rows in the dataframe df_this     
# df_this (pd.dataframe), the pandas dataframe storing all the data
# decimalLatitude (float), the name (string) of the column that stores the decimalLatitude (float)
# decimalLongitude (float), the name (string) of the column that stores the decimalLongitude (float)
# country (string), the name (string) of the column that stores the country name (string)
# stateProvince (string), the name (string) of the column that stores the state or province name (string)
# municipality (string), the name (string) of the column that stores the municipality name (string)
# locality (string), the name (string) of the column that stores the locality name (string)
# this_ind (int), if for some reasons, the georef check function doesn't run till the last row in the last run, input the index (int) of the row that causes the problem, and this time we start from that row.
# user_agent (string): used for calling google translator, I used my email here
    warnings.filterwarnings("ignore")
    for ind in df_this.index:
        geolocator = Nominatim(user_agent=user_agent+":"+str(ind))
        
        if not np.isnan(this_ind):
            if ind < this_ind:
                continue

        if np.isnan(df_this[decimalLatitude][ind]):
            All_the_same = False
            same_municipality = False
            same_state = False
            same_country = False
            print("no coordinates")
            df_this["coordinate reliability"][ind] = "no coordinates"
            continue

        else:
            try:
                location = geolocator.reverse(str(df_this[decimalLatitude][ind])+","+str(df_this[decimalLongitude][ind]),language="en")

                address = location.raw['address']
            except AttributeError:
                df_this["coordinate reliability"][ind] = "not on land"
                continue
            except:
                print("something wrong!")
                print(ind)
                print(df_this[decimalLatitude][ind])
                print(df_this[decimalLongitude][ind])
                return ind
                



            key_list=np.array(list(address.keys()))


            state_where = np.where(key_list == 'state')[0]


            this_country = address.get('country', '')
            this_state = address.get('state', '')
            record_country = str(df_this[country][ind])
            record_state = str(df_this[stateProvince][ind])
            record_municipality = str(df_this[municipality][ind])
            record_locality = str(df_this[locality][ind])
#             print('country'+str(record_country)+', state:'+str(record_state) +', municipality:'+str(record_municipality)+', locality:'+str(record_locality))
            

#             print(type(record_locality))


            All_the_same = False
            same_country = False
            translate_M = False

            try:
                if not pd.isnull(record_country):
                    if record_country == this_country:
                        same_country = True 
                    elif unidecode(address.get('country', '')).strip() == unidecode(this_country).strip():
                        same_country = True
            except RuntimeError:
                print('Run Time Error - translate country - '+address.get(this_key, ''))

            if same_country:
                if pd.isnull(record_locality):
                    break
                count_num = state_where - 1
                while count_num >= 0:
                    this_key = key_list[count_num][0]
                    this_item = address.get(this_key, '')
                    #print(type(this_item))

                    if (record_locality in this_item) or (this_item in record_locality):
                        All_the_same = True
                    else:
                        try:
                            this_item = unidecode(this_item)
                            record_locality = unidecode(record_locality)
                        except RuntimeError:
                            print('Run Time Error - translate locality - '+address.get(this_key, ''))

                        if (record_locality in this_item) or (this_item in record_locality):
                            All_the_same = True
    
                    count_num = count_num - 1


        if same_country:
            if All_the_same:
                #print("all agree")
                df_this["coordinate reliability"][ind] = "all agree"
            else:
                #print("Location different")
                df_this["coordinate reliability"][ind] = "Location different - no state&municipio record"
        else:
            #print("Country different")
            df_this["coordinate reliability"][ind] = "Country different"
    
    return -1

def pre_process_df_stavana(raw_csv_path,my_email,csv_saving_path):
    # raw_csv_path (string): path to the raw csv file
    # my_email (string): the email address fed to google translator for georef checking
    # csv_saving_path (string): path to save the processed csv file

    df_test4 = pd.read_csv(raw_csv_path)
    df_species_4 = pd.DataFrame(columns=species_feature_list)
    df_species_4['Genus'] = df_test4[['Genus']].copy()
    df_species_4['Species'] = df_test4[['Species']].copy()
    df_species_4['Subspecies'] = df_test4[['Subspecies']].copy()

    df_species_4['count'] = df_test4[['Abundance']].copy()



    df_species_4['Location'] = df_test4[['Location']].copy()
    df_species_4['Country'] = df_test4[['Country']].copy()


    df_species_4['DecimalLatitude'] = df_test4[['Latitude']].copy()
    df_species_4['DecimalLongitude'] = df_test4[['Longitude']].copy()

    df_species_4['Comments on coordinates'] = df_test4[['Location Notes']].copy()

    df_species_4['year-begin'] = df_test4[['Initial Year']].copy()
    df_species_4['month-begin'] = df_test4[['Initial Month']].copy()
    df_species_4['day-begin'] = df_test4[['Initial Day']].copy()

    df_species_4['year-end'] = df_test4[['Final Year']].copy()
    df_species_4['month-end'] = df_test4[['Final Month']].copy()
    df_species_4['day-end'] = df_test4[['Final Day']].copy()



    df_species_4['Primary Collector info'] = df_test4[['Reference']].copy()
    df_species_4['Secondary Collector info'] = 'Alexander Moffett, The University of Texas'

    df_species_state = np.nan
    while df_species_state != -1:
        df_species_state = check_georef_stavana(df_species_4,'DecimalLatitude','DecimalLongitude', 'Country', 'StateProvince','MunicipioCounty', 'Location',df_species_state,my_email)
        time.sleep(1)

    df_species_4.to_csv(csv_saving_path)
    print("success")



# new America dataset
    
def code_to_country(this_list):
    new_list = np.array([])
    for i in this_list:
        #print(i)
        if pd.isnull(i):
            new_list = np.append(new_list,np.nan)
        else:
            #print(pycountry.countries.get(alpha_2=i).name)
            new_list = np.append(new_list,pycountry.countries.get(alpha_2=i).name)
            
    
    return new_list
    




def check_georef_multi_core(df_this,decimalLatitude,decimalLongitude, country, stateProvince,municipality, locality, this_ind, end_ind,user_agent):
# Check if their coordinates indicate the same county, state, country information as the corresponding record.
        
    #translation = translator.translate("Good Morning!")
    
    warnings.filterwarnings("ignore")
    for ind in df_this.index:
        geolocator = Nominatim(user_agent=user_agent+":"+str(ind),timeout=3)
        
        if not np.isnan(this_ind):
            if ind < this_ind:
                continue
                
            if ind >end_ind:
                return -2

        if np.isnan(df_this[decimalLatitude][ind]):
            All_the_same = False
            same_municipality = False
            same_state = False
            same_country = False
            print("no coordinates")
            df_this["coordinate reliability"][ind] = "no coordinates"
            continue

        else:
            try:
                location = geolocator.reverse(str(df_this[decimalLatitude][ind])+","+str(df_this[decimalLongitude][ind]),language="en")

                address = location.raw['address']

            except AttributeError:
                df_this["coordinate reliability"][ind] = "not on land"
                continue
            except Exception as error:
                print("something wrong!")
                print(ind)
                print(df_this[decimalLatitude][ind])
                print(df_this[decimalLongitude][ind])
                print(error)
                return ind
                



            key_list=np.array(list(address.keys()))


            state_where = np.where(key_list == 'state')[0]


            this_country = address.get('country', '')
            this_state = address.get('state', '')
            record_country = str(df_this[country][ind])
            record_state = str(df_this[stateProvince][ind])
            record_municipality = str(df_this[municipality][ind])
            record_locality = str(df_this[locality][ind])
#             print('country'+str(record_country)+', state:'+str(record_state) +', municipality:'+str(record_municipality)+', locality:'+str(record_locality))
            

#             print(type(record_locality))


            All_the_same = False
            same_municipality = False
            same_state = False
            same_country = False
            translate_M = False

            try:
                if not pd.isnull(record_country):
                    if record_country == this_country:
                        same_country = True 
                    elif unidecode(address.get('country', '')).strip() == unidecode(this_country).strip():
                        same_country = True

            except RuntimeError:
                print('Run Time Error - translate country - '+address.get(this_key, ''))

            if same_country:
                if not pd.isnull(record_state):
                    if (record_state in this_state) or (this_state in record_state):
                        same_state = True
                    else:
                        try:
                            this_state = unidecode(this_state)
                            record_state = unidecode(record_state)
                        except RuntimeError:
                            print('Run Time Error - translate state - '+address.get(this_key, ''))
                        if (record_state in this_state) or (this_state in record_state):
                            same_state = True
            # iterate over all the 'smaller' keys. decide if the finest location is recorded correctly.
            if same_state:
                if not pd.isnull(record_municipality):
                    count_num = state_where - 1
                    while count_num >= 0:
                        this_key = key_list[count_num][0]
                        this_item = address.get(this_key, '')
                        #print(type(this_item))
                        if same_municipality:
                            if (record_locality in this_item) or (this_item in record_locality):
                                All_the_same = True
                            else:
                                try:
                                    this_item = unidecode(this_item)
                                    record_locality = unidecode(record_locality)
                                except RuntimeError:
                                    print('Run Time Error - translate locality - '+address.get(this_key, ''))

                                if (record_locality in this_item) or (this_item in record_locality):
                                    All_the_same = True

                        else:# see if same municipality
                            if (record_municipality in this_item) or (this_item in record_municipality):
                                same_municipality = True
                            else:
                                try:
                                    if not translate_M:
                                        record_municipality = unidecode(record_municipality)
                                        translate_M = True
                                    this_item = unidecode(this_item)
                                except RuntimeError:
                                    print('Run Time Error - translate municipality - '+address.get(this_key, ''))

                                if (record_municipality in this_item) or (this_item in record_municipality):
                                    same_municipality = True
                                    if pd.isnull(record_locality):
                                        break

                        count_num = count_num - 1
                


        if same_country:
            if same_state:
                if same_municipality:
                    if All_the_same:
                        #print("all agree")
                        df_this["coordinate reliability"][ind] = "all agree"
                    else:
                        #print("Location different")
                        df_this["coordinate reliability"][ind] = "Location different"
                else:
                    #print("MunicipioCounty different")
                    df_this["coordinate reliability"][ind] = "MunicipioCounty different"

            else:
                #print("StateProvince different")
                df_this["coordinate reliability"][ind] = "StateProvince different"
        else:
            #print("Country different")
            df_this["coordinate reliability"][ind] = "Country different"
    
    return -1

def check_georef_multi_layer(df_this,decimalLatitude,decimalLongitude, country, stateProvince,municipality, locality, this_ind, end_ind,my_email):
    df_species_state = this_ind
    while df_species_state != -1:
        df_species_state = check_georef_multi_core(df_this,decimalLatitude,decimalLongitude, country, stateProvince,municipality, locality,df_species_state,end_ind,my_email)
        time.sleep(1)

def pre_process_df_new_america(raw_csv_path,my_email,csv_saving_path):
    # raw_csv_path (string): path to the raw csv file
    # my_email (string): the email address fed to google translator for georef checking
    # csv_saving_path (string): path to save the processed csv file
    df_newa0 = pd.read_csv(raw_csv_path)
    df_newa = pd.DataFrame(columns=species_feature_list)

    df_newa['Genus'] = df_newa0[['genericName']].copy()
    df_newa['Species'] = df_newa0[['specificEpithet']].copy()
    df_newa['Subspecies'] = df_newa0[['infraspecificEpithet']].copy()
    df_newa['Sex'] = df_newa0[['sex']].copy()
    df_newa['Habitat'] = df_newa0[['habitat']].copy()
    df_newa['Collection Method'] = df_newa0[['basisOfRecord']].copy()
    df_newa['count'] = df_newa0[['individualCount']].copy()
    df_newa['observation comment'] = 'samplingProtocol:'+df_newa0['samplingProtocol'].copy()+'----samplingEffort:'+df_newa0['samplingEffort'].copy()

    df_newa['DecimalLatitude'] = df_newa0[['decimalLatitude']].copy()
    df_newa['DecimalLongitude'] = df_newa0[['decimalLongitude']].copy()

    df_newa['Location'] = df_newa0['locality'].copy()+', '+df_newa0['verbatimLocality'].copy()
    df_newa['MunicipioCounty'] = df_newa0[['municipality']].copy()
    df_newa['StateProvince'] = df_newa0[['stateProvince']].copy()
    df_newa['Country'] = code_to_country(df_newa0['countryCode'].copy())

    df_newa['georeferenceSources'] = df_newa0[['georeferenceSources']].copy()
    df_newa['positional_accuracy'] = df_newa0[['coordinateUncertaintyInMeters']].copy()


    df_newa['Primary Collector info'] = df_newa0['recordedBy'].copy().astype(str) +'----'+df_newa0['associatedReferences'].copy().astype(str) 

    df_newa['Secondary Collector info'] = 'Ceccarelli S, Balsalobre A, Cano M E, Vicente M E, Rabinovich J E, Medone P, Rocchi V M, Galliari J G, Marti G A (2022). Datos de ocurrencia de triatominos americanos del Laboratorio de Triatominos del CEPAVE (CONICET-UNLP). Version 1.6. Centro de Estudios Parasitológicos y de Vectores (CEPAVE). Occurrence dataset https://doi.org/10.15468/fbywtn accessed via GBIF.org on 2023-03-30.'

    df_newa['year-begin'] = df_newa0[['year']].copy().fillna(0)
    df_newa['month-begin'] = df_newa0['month'].copy().fillna(0)
    df_newa['day-begin'] = df_newa0[['day']].copy().fillna(0)



    df_newa['data quality'] = df_newa0[['issue']].copy()
    
    df_species_state = np.nan
    while df_species_state!= -1:
        df_species_state = check_georef(df_newa,'DecimalLatitude','DecimalLongitude', 'Country', 'StateProvince','MunicipioCounty', 'Location',df_species_state,my_email)
        time.sleep(1)
    # processes = []

    # df_list = np.array_split(df_newa, 40)
    # total_df_length = len(df_list)
    # for i in range(0,40):
    #     ind_start = i*490
    #     ind_end = (i+1)*490-1
    #     p = multiprocessing.Process(target=check_georef_multi_layer, args=(df_list[i],'DecimalLatitude','DecimalLongitude', 'Country', 'StateProvince','MunicipioCounty', 'Location',ind_start,ind_end,my_email))
    #     processes.append(p)
    #     p.start()

    # for process in processes:
    #     process.join()
        
        
    # df_newa = pd.concat(df_list, axis=0)
    
    df_newa.to_csv(csv_saving_path)


# Paty's data
    
def month_digit(month):
    if not isinstance(month, str):
        return np.nan
    month = month.lower()
    if month == "january":
        return 1
    if month == "february":
        return 2
    if month == "march":
        return 3
    if month == "april":
        return 4
    if month == "may":
        return 5
    if month == "june":
        return 6
    if month == "july":
        return 7
    if month == "august":
        return 8
    if month == "september":
        return 9
    if month == "october":
        return 10
    if month == "november":
        return 11
    if month == "december":
        return 12
    if '/' in month:
        return month
    return np.nan

def month_digit_all(month_all):
    this_list = np.array([])
    for i in month_all:
        this_list = np.append(this_list,month_digit(i))
    
    return this_list

def pre_process_df_paty(raw_csv_path,my_email,csv_saving_path):
    # raw_csv_path (string): path to the raw csv file
    # my_email (string): the email address fed to google translator for georef checking
    # csv_saving_path (string): path to save the processed csv file
    df_paty0 = pd.read_csv(raw_csv_path)
    df_paty = pd.DataFrame(columns=species_feature_list)
    df_paty['Genus'] = df_paty0[['Genus']].copy()
    df_paty['Species'] = df_paty0[['Species']].copy()
    df_paty['DecimalLatitude'] = df_paty0[['Latitude']].copy()
    df_paty['DecimalLongitude'] = df_paty0[['Longitude']].copy()
    df_paty['Sex'] = df_paty0[['Sex']].copy()
    df_paty['Primary Collector info'] = df_paty0['CollectorI'].copy().astype(str) +'-'+df_paty0['PubNotes'].copy().astype(str) 
    df_paty['Location'] = df_paty0[['Location']].copy()
    df_paty['MunicipioCounty'] = df_paty0[['TexasCount']].copy()
    df_paty['Country'] = 'United States'
    df_paty['StateProvince'] = 'Texas'
    df_paty['Natural infection information'] = df_paty0[['Infection']].copy()
    df_paty['Habitat'] = df_paty0[['HabitatTyp']].copy()
    df_paty['observation comment'] = df_paty0['comments'].copy()+'-LocationTE:'+df_paty0['LocationTe'].copy()+'-ProcotolUs:'+df_paty0['ProcotolUs'].copy()+'-BMA_Date:'+df_paty0['BMA_Date'].copy()+'-Bloodmeal:'+df_paty0['Bloodmeal'].copy()+'-PCRDate'+df_paty0['PCRDate'].copy()
    df_paty['Collection Method'] = df_paty0[['Collection']].copy()
    df_paty['Secondary Collector info'] = 'Teresa Patricia Feria'

    df_paty['year-begin'] = df_paty0[['YearCollec']].copy().fillna(0)
    df_paty['month-begin'] = month_digit_all(df_paty0['MonthColle'].copy())
    df_paty['day-begin'] = df_paty0[['DayCollect']].copy().fillna(0)

    df_species_state = np.nan
    while df_species_state!= -1:
        df_species_state = check_georef(df_paty,'DecimalLatitude','DecimalLongitude', 'Country', 'StateProvince','MunicipioCounty', 'Location',df_species_state,my_email)


    df_paty.to_csv(csv_saving_path)


# Alejandro's data

def pre_process_df_Alejandro(raw_csv_path,my_email,csv_saving_path):
    df_alejandro = pd.read_csv(raw_csv_path)
    df_species_state = np.nan
    df_alejandro['DecimalLatitude'].astype(float)
    df_alejandro['DecimalLongitude'].astype(float)
    while df_species_state!= -1:
        df_species_state = check_georef(df_alejandro,'DecimalLatitude','DecimalLongitude', 'Country', 'StateProvince','MunicipioCounty', 'Location',df_species_state,my_email)
    
    df_alejandro.to_csv(csv_saving_path)


# New Collect data

def pre_process_df_new_collect(raw_csv_path,my_email,csv_saving_path):
    df_new_collect = pd.read_csv(raw_csv_path)
    df_species_state = np.nan
    while df_species_state!= -1:
        try:
            df_species_state = check_georef(df_new_collect,'DecimalLatitude','DecimalLongitude', 'Country', 'StateProvince','MunicipioCounty', 'Location',df_species_state,my_email)   
        except:
            print('error')
            print(df_species_state)
            print(df_new_collect['DecimalLatitude'])
            break
    df_new_collect.to_csv(csv_saving_path)





"""
For combine files, check duplicates, and generate products
"""

# Check for duplication of record

def check_dup(df_this):
    this_length = len(df_this['DecimalLatitude'])
    for ind in df_this.index:
        #print(df_this['duplication'][ind])
        #print(type(df_this['duplication'][ind]))
        if not pd.isnull(df_this['duplication'][ind]):
            continue
        if pd.isnull(df_this['DecimalLatitude'][ind]):
            continue
        if pd.isnull(df_this['year-begin'][ind]):
            continue
        
        this_lat = np.ones(this_length)*df_this['DecimalLatitude'][ind]
        this_lon = np.ones(this_length)*df_this['DecimalLongitude'][ind]
        this_year = np.ones(this_length)*df_this['year-begin'][ind]
        all_other_lat = np.array(df_this['DecimalLatitude'])
        all_other_lon = np.array(df_this['DecimalLongitude'])
        all_other_year = np.array(df_this['year-begin'])
        
        diff_distance = np.absolute(np.square(this_lat-all_other_lat)+np.square(this_lon-all_other_lon))
        diff_year = np.absolute(np.square(this_year-all_other_year))
        index_suspect = np.intersect1d(np.where( diff_distance < 0.001),np.where(diff_year < 1))
        #print(index_suspect)
        
        this_species = df_this['Species'][ind]
        
        for this_index in index_suspect:
            if this_index == ind:
                continue
            if this_species == df_this['Species'][this_index]:
                df_this['duplication'][ind]= index_suspect.astype(object)
                #print('duplicate warning')
        
def create_separate_csv_America(bug_name, df_all, saving_path):
    df_result = df_all[df_all['Species'] == bug_name].copy()
    for i in df_result.index:
        if pd.isnull(df_result['DecimalLongitude'][i]):
            continue        
        if len(str(df_result['DecimalLongitude'][i]).split(".")[1]) >=3:
            #print('select')
            #print(df_result['coordinate reliability'][i])
            this_location = df_result['coordinate reliability'][i]
            if (this_location == 'all agree' or this_location == 'Location different') or this_location=='MunicipioCounty different':
                df_all['select for 2023 model'][i]=True
                df_result['select for 2023 model'][i]=True
                
    #print(df_result)
    df_thisbug = df_result[df_result['select for 2023 model']==True].copy()
    if df_thisbug.empty or len(df_thisbug) == 0:
        return
    df_thisbug.to_csv(saving_path+bug_name+'.csv')


def create_separate_csv_northAmerica(bug_name, df_all, saving_path):
    df_result = df_all[df_all['Species'] == bug_name].copy()
    for i in df_result.index:
        if pd.isnull(df_result['DecimalLongitude'][i]):
            continue     
        if pd.isnull(df_result['Country'][i]):
            continue    
        if len(str(df_result['DecimalLongitude'][i]).split(".")[1]) >=3:
            #print('select')
            #print(df_result['coordinate reliability'][i])
            this_location = df_result['coordinate reliability'][i]
            if (this_location == 'all agree' or this_location == 'Location different') or this_location=='MunicipioCounty different':
                df_all['select for 2023 model'][i]=True
                df_result['select for 2023 model'][i]=True
                
    #print(df_result)
    df_thisbug = df_result[(df_result['select for 2023 model']==True) &((df_result['Country']=='United States')|(df_result['Country']=='Mexico'))].copy()
    if df_thisbug.empty or len(df_thisbug) == 0:
        return
    df_thisbug.to_csv(saving_path+'northAmerica_'+bug_name+'.csv')

def combine_all_check_duplicate_and_save(input_dataframe_paths,final_csvs_saving_dir):
    frames = []
    for this_path in input_dataframe_paths:
        this_frame = pd.read_csv(this_path)
        frames.append(this_frame)
    
    df_species = pd.concat(frames, axis=0)
    df_species=df_species.reset_index()
    df_species=df_species[species_feature_list].copy()
    print("species keys")
    print(df_species.keys())
    df_species['id'] = df_species.index
    df_species['Country'] = df_species['Country'].replace(['México'], 'Mexico')

    df_species["duplication"] = np.nan
    check_dup(df_species)
    sp_rarefied_name_list_part = ['sanguisuga','rubida','recurva','protracta','mexicana','mazzottii','neotomae','longipennis','lecticularia','indictiva','gerstaeckeri','dimidiata']

    for this_name in sp_rarefied_name_list_part:
        create_separate_csv_America(this_name, df_species, final_csvs_saving_dir)
        create_separate_csv_northAmerica(this_name, df_species, final_csvs_saving_dir)

    print("success")


def combine_all_check_duplicate_and_save_edit(input_dataframe_paths,final_csvs_saving_dir):
    frames = []
    for this_path in input_dataframe_paths:
        this_frame = pd.read_csv(this_path)
        frames.append(this_frame)
    
    df_species = pd.concat(frames, axis=0)
    df_species=df_species.reset_index()
    df_species=df_species[species_feature_list].copy()
    print("species keys")
    print(df_species.keys())
    df_species['id'] = df_species.index
    df_species['Country'] = df_species['Country'].replace(['México'], 'Mexico')

    df_species["duplication"] = np.nan
    check_dup(df_species)
    sp_rarefied_name_list_part = df_species['Species'].unique()#['sanguisuga','rubida','recurva','protracta','mexicana','mazzottii','neotomae','longipennis','lecticularia','indictiva','gerstaeckeri','dimidiata']

    for this_name in sp_rarefied_name_list_part:
        print(this_name)
        try:
            create_separate_csv_America(str(this_name), df_species, final_csvs_saving_dir)
            create_separate_csv_northAmerica(str(this_name), df_species, final_csvs_saving_dir)
        except:
            print('error')

    print("success")


def create_separate_csv_America_edit(bug_name, df_all, saving_path):
    df_result = df_all[df_all['Species'] == bug_name].copy()
    for i in df_result.index:
        if pd.isnull(df_result['DecimalLongitude'][i]):
            continue        
        if len(str(df_result['DecimalLongitude'][i]).split(".")[1]) >=3:
            #print('select')
            #print(df_result['coordinate reliability'][i])
            this_location = df_result['coordinate reliability'][i]
            if (this_location == 'all agree' or this_location == 'Location different') or this_location=='MunicipioCounty different':
                df_all['select for 2023 model'][i]=True
                df_result['select for 2023 model'][i]=True
                
    #print(df_result)
    df_thisbug = df_result[df_result['select for 2023 model']==True].copy()
    if df_thisbug.empty or len(df_thisbug) == 0:
        return
    
    print(bug_name)
    print(len(df_thisbug))
    if len(df_thisbug) >= 30:
        df_thisbug.to_csv(saving_path+bug_name+'.csv')
    return df_thisbug
    


def create_separate_csv_northAmerica_edit(bug_name, df_all, saving_path):
    df_result = df_all[df_all['Species'] == bug_name].copy()
    for i in df_result.index:
        if pd.isnull(df_result['DecimalLongitude'][i]):
            continue     
        if pd.isnull(df_result['Country'][i]):
            continue    
        if len(str(df_result['DecimalLongitude'][i]).split(".")[1]) >=3:
            #print('select')
            #print(df_result['coordinate reliability'][i])
            this_location = df_result['coordinate reliability'][i]
            if (this_location == 'all agree' or this_location == 'Location different') or this_location=='MunicipioCounty different':
                df_all['select for 2023 model'][i]=True
                df_result['select for 2023 model'][i]=True
                
    #print(df_result)
    df_thisbug = df_result[(df_result['select for 2023 model']==True) &(((df_result['Country']=='United States')|(df_result['Country']=='Mexico'))|(df_result['Country']=='Canada'))].copy()

    if df_thisbug.empty or len(df_thisbug) == 0:
        return
    
    print(bug_name)
    print(len(df_thisbug))
    if len(df_thisbug) >= 30:
        df_thisbug.to_csv(saving_path+'northAmerica_'+bug_name+'.csv')
    return df_thisbug
    


def combine_all_check_duplicate_and_save_edit2(input_dataframe_paths, final_csvs_saving_dir):
    frames = []
    for this_path in input_dataframe_paths:
        this_frame = pd.read_csv(this_path)
        frames.append(this_frame)
    
    df_species = pd.concat(frames, axis=0)
    df_species = df_species.reset_index()
    df_species = df_species[species_feature_list].copy()
    print("species keys")
    print(df_species.keys())
    df_species['id'] = df_species.index
    df_species['Country'] = df_species['Country'].replace(['México'], 'Mexico')

    df_species["duplication"] = np.nan
    check_dup(df_species)
    sp_rarefied_name_list_part = df_species['Species'].unique()  # Adjust list as needed

    all_america_df = []
    all_north_america_df = []

    for this_name in sp_rarefied_name_list_part:
        print(this_name)
        try:
            america_df = create_separate_csv_America_edit(str(this_name), df_species, final_csvs_saving_dir)
            if america_df is not None:
                all_america_df.append(america_df)
                
            north_america_df = create_separate_csv_northAmerica_edit(str(this_name), df_species, final_csvs_saving_dir)
            if north_america_df is not None:
                all_north_america_df.append(north_america_df)
        except Exception as e:
            print(f'Error processing {this_name}: {e}')

    if all_america_df:
        combined_america_df = pd.concat(all_america_df, axis=0)
        #combined_america_df.to_csv(final_csvs_saving_dir + 'combined_america.csv', index=False)

    if all_north_america_df:
        combined_north_america_df = pd.concat(all_north_america_df, axis=0)
        #combined_north_america_df.to_csv(final_csvs_saving_dir + 'combined_north_america.csv', index=False)

    print("success")
    return combined_america_df, combined_north_america_df


















