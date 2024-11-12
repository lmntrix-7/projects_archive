XYZprofile<-function(ID){
  if(ID >= 202400000 || ID <=200000000) stop("Wrong LSE Student ID!")
  set.seed(ID)
  gender = sample(c("Male","Female"),1)
  age = sample(17:25,1)
  locations = c("Ashfield", "Ashford (London Middlesex)", "Atherton (Manchester)", "Banbury", "Barking (London)", "Barnet (London)", "Barnsley", 
   "Basildon", "Basingstoke", "Belvedere (London)", "Birmingham (Garretts Green)", "Birmingham (Kings Heath)", "Birmingham (Kingstanding)", "Birmingham (Shirley)", 
   "Birmingham (South Yardley)", "Birmingham (Sutton Coldfield)", "Bishops Stortford", "Blackburn with Darwen", "Blackpool", "Bletchley", "Blyth", "Bolton (Manchester)", 
   "Borehamwood (London)", "Bournemouth", "Bradford (Heaton)", "Bradford (Thornbury)", "Bredbury (Manchester)", "Bristol (Brislington)", "Bristol (Kingswood)", "Bristol (Southmead)", 
   "Burgess Hill", "Burton on Trent", "Bury (Manchester)", "Camborne", "Cambridge (Chesterton Road)", "Cambridge (Cowley Road)", "Cardiff (Llanishen)", "Cardington", 
   "Cheetham Hill (Manchester)", "Cheltenham", "Chertsey (London)", "Chester", "Chichester", "Chingford (London)", "Chorley", "Colchester", "Coventry", "Crawley", "Croydon (London)", 
   "Darlington", "Doncaster", "Dorchester", "Dundee", "Durham", "Eastbourne", "Edinburgh (Currie)", "Edinburgh (Musselburgh)", "Elswick", "Enfield (London)", "Erith (London)", "Exeter", 
   "Failsworth (Manchester)", "Farnborough", "Garston (Liverpool)", "Gateshead", "Gillingham", "Glasgow (Anniesland)", "Glasgow (Baillieston)", "Glasgow (Shieldhall)", "Gloucester", 
   "Goodmayes (London)", "Greenford (London)", "Guildford", "Halifax", "Hamilton", "Hayes (London)", "Heckmondwike", "Hendon (London)", "Herne Bay", "High Wycombe", "Hither Green (London)",
   "Hornchurch (London)", "Horsforth", "Huddersfield", "Hyde (Manchester)", "Ipswich", "Isleworth (London)", "Kettering", "Kirkcaldy", "Lee On The Solent", "Leeds", "Leicester (Wigston)", 
   "Lichfield", "Lincoln", "Loughton (London)", "Lower Gornal", "Luton", "Maidstone", "Middlesbrough", "Mill Hill (London)", "Mitcham (London)", "Morden (London)", "Nelson", 
   "Newport (Gwent)", "Norris Green (Liverpool)", "Northampton", "Norwich", "Nottingham (Colwick)", "Oxford (Cowley)", "Paisley", "Peterborough", "Pinner (London)", 
   "Plymouth", "Pontefract", "Pontypridd", "Portsmouth", "Preston", "Reading", "Reigate", "Rochdale (Manchester)", "Rotherham", "Sale (Manchester)", "Sheffield (Handsworth)", 
   "Sheffield (Middlewood Road)", "Sidcup (London)", "Slough (London)", "South Shields", "Southall (London)", "Southampton (Forest Hills)", "Southampton (Maybush)", 
   "Southend-on-Sea", "Southport (Liverpool)", "St Albans", "St Helens (Liverpool)", "Stoke-On-Trent (Cobridge)", "Stoke-on-Trent (Newcastle-Under-Lyme)", "Sunderland", 
   "Sutton (London)", "Swansea", "Swindon", "Taunton", "Telford", "Tilbury", "Tolworth (London)", "Upton", "Uxbridge (London)", "Wakefield", "Wanstead (London)", "Warwick", 
   "Watford", "Wednesbury", "West Didsbury (Manchester)", "West Wickham (London)", "Wolverhampton", "Worcester", "Worksop", "Worthing", "York")
  centre = sample(locations,1)
  cat(paste("The profile of XYZ:", paste("- Age: ", age), paste("- Gender: ", gender), paste("- Home address: ", centre), "" ,sep="\n"))
}
