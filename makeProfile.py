from models import HistoricalFundamentals, Profile, ProfileOfficer


def makeProfile(data: HistoricalFundamentals) -> Profile:
    profile = Profile()
    profile.name = data.General.Name
    profile.sector = data.General.Sector
    profile.industry = data.General.Industry
    profile.description = data.General.Description
    profile.address = data.General.Address
    profile.phone = data.General.Phone
    profile.webUrl = data.General.WebURL

    profile.officers = []
    for key in data.General.Officers:
        officer = ProfileOfficer()
        officer.name = data.General.Officers[key].Name
        officer.title = data.General.Officers[key].Title
        officer.yearBorn = data.General.Officers[key].YearBorn
        profile.officers.append(officer)

    return profile
