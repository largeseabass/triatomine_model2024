library( spThin )


#bug_list <- list("sanguisuga","rubida","recurva","protracta","neotomae","mexicana","mazzottii",'barberi',"longipennis","lecticularia","indictiva","gerstaeckeri","dimidiata")

new_bug_list <- list('picturata','neotomae')#('gerstaeckeri',"sanguisuga","dimidiata","protracta","rubida","longipennis",'pallidipennis','barberi',"mexicana","lecticularia","indictiva","mazzottii","recurva",'maxima','phyllosoma','hirsuta')

for (this_bug in new_bug_list){
  # to get a full path name: e.g. /your_path/final_data/northAmerica_sanguisuga.csv
  raw_bug_data_path <- paste("/your_path/final_data/northAmerica_",this_bug,'.csv',sep = '')
  # read the csv file into the variable raw_data
  raw_data <- read.csv(raw_bug_data_path)
  # we call the thin function here. 
  thinned_dataset_full <-thin(loc.data = raw_data, 
                              lat.col = "DecimalLatitude", long.col = "DecimalLongitude", 
                              spec.col = "Species", 
                              thin.par = 5, reps = 10, 
                              locs.thinned.list.return = TRUE, 
                              max.files = 1, 
                              out.dir = "/your_path/spthin/", out.base = this_bug, #modify
                              write.log.file = FALSE)
}

# all the following lines you can ignore
files <- list.files(path = "/your_path/spthin/", pattern = "*.csv", full.names = FALSE)
old_names <- list.files(path = "/your_path/spthin/", pattern = "*.csv", full.names = TRUE)
new_names <- paste("/your_path/spthin/",substr(files,1,3),'.csv',sep = '')
file.rename(from = old_names, to = new_names)


