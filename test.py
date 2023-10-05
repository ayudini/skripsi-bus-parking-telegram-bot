res = {"location": {
        "latitude": -7.8016936,
        "longitude": 110.3658478
    }}
destination_coor = ",".join([str(coor) for coor in res['location'].values()])
print(destination_coor)