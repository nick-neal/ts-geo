# ts-geo

## Description

This is the micro service that handles calling google maps and returning relevant direction data, as well as picking out geo-points for gathering weather data.  

## setting up API KEYS
Due to security, you will need to create a new file: `app/config/tskeys.py`

add the following to the new file:

```
from config.tsconfig import APP_ENV

### API KEYS ###

if APP_ENV == "DEV":
    G_DIRECTIONS_API_KEY = '<Google Maps Directions API Key>'

```

## Running in docker

**You will need docker installed on your computer to run the code**

you are going to need to `cd` in to the directory you have pulled the code to. Once you are there, go ahead and run the following commands based on your needs.

`make build`
This will build the docker container where you will run the code.

`make run`
This will run the container and allow you to interact with the API.

`make inspect`
**container must be running** This will allow you to open a shell in the container for viewing log files and debugging configurations.

`make stop`
This will stop the running container.

`make clean`
This will purge the docker registry of this container.

## API
For app name and version, query *http://127.0.0.1:4081/*

The api will be located at *http://127.0.0.1:4081/ts-geo*

### `/route/{start_addr}/{end_addr}/{trans_id} [GET]`

This is used to pull direction data from google maps, and build out an array of geo-points to gather weather data on.

##### Request
Var Name | Var Type | Description
-------- | -------- | -----------
start_addr | String | This is the starting address for your route.
end_addr | String | This is the destination address for your route.
trans_id | String | used for tracking and debugging requests accross micro services.

##### Response (json)
Var Name | Var Type | Description
-------- | -------- | -----------
data | Object | This carries all geo-location and weather data.
data -> distance | int | This is the distance of the route measured in meters.
data -> duration | int | This is the time it would take to travel the route measured in seconds.
data -> geo_spacers | float arrays | These are geo-coordinate arrays along the route that weather data will be pulled for.
data -> polyline | String | This is an encoded string containing geo-coordinates that will draw the route line on a map.
data -> weather_data | Object Array | This is an array containing weather data from the geo-coordinates in the data -> geo_spacers array.
end_addr | String | This is the destination address for your route.
start_addr | String | This is the starting address for your route.
status | String | "OK" means the application was able to complete the request with no issues. any other response means an error occured, and the integrity of any data may be compromised.

```
/route/Denver,+CO/Grand+Junction,+CO/abc123

{
  "data": {
    "distance": 391649,
    "duration": 14598,
    "geo_spacers": [
      [
        39.74116,
        -104.98791
      ],
      [
        39.66086,
        -105.9867
      ],
      [
        39.6728,
        -106.79992
      ],
      [
        39.51916,
        -107.85143
      ],
      [
        39.06437,
        -108.55076
      ]
    ],
    "polyline": "g}pqFlmx_Sdu@aBfTxC`@bTrJ~t@`GpOt@~nBq@`fD`An~Ow@ddHbo@bt@jcCnkBrBjgAoY`aCwV`wC_~@rcHjkAvxBiEvv@ak@|`AqVvrByJneB_AnhA}Yj{@as@lnBasAxw@eTf[nIla@`Ctz@cUfhAlMpyC`Yh_AsDt|@kFrgB_aA~pDkaArnDmJl{DjJ|yCrTv_Brj@rn@pm@vkBnm@fs@nmBj{@bdA|Jlt@haAlg@~nCuKnsCrGduElNl~A{Kv_Cqf@~{A{BtmBjp@`uBvgAtnArB|o@dO`dCvIfdC~Sn|ChZr}@ru@dfAlr@pdDvm@zkBxcA`pCdn@hkBl`@dNbi@IzYv`@zhAbnAjeA`|AtzA`o@va@p~@j}AnhAt~@zZ|]hOdc@gW|^iA`Zzb@veAmBt`@~HrJh{AgFhqAoQrhBZlr@qXhXmqAvhAkqANy|BbyAcvBvvBymAuTmd@|u@gShfBckAtl@osBdNyoAflC}_@zhCbYjwChD`{BkTxfBjVnnAhwAbmCpx@hsAv_@ty@|\\tY}G~u@{k@`]ka@tkCuaBtrFgLfu@lNjhAi]|yBmHx}AoUj`@gh@ttCwJndBcGh{@}_@tq@ioB|o@uJrh@sdAp{@sm@teCk{@ju@hB~iBj`@fvA|iAnxB|y@b_A|Ux`AjL~cAr`@heCheBvoEpK~zAzM`fHgKthChDv_EcSlgDdm@lqDdZtwCyYl{DnVb}B|s@|eB|[~n@pa@jKhMnoAoA`\\bd@h]n]zxAxd@xwAf[dW`Nn}@n{@`eAh^xgBlm@dn@nIpdBfg@vX~p@bpAt[zr@o[piAcVhdA~@ja@xXhTh@r|@}@pcBfa@~_Arn@~v@wt@jrAsUxbC|@`uBzN~lB{YzmAy\\znBwn@vqA~KpaBbLv\\mOxs@nUxkB`Wxx@cAr~AaZpvBzRdtBr~@rzAbqAvpNoBxrDjmAxzDnJj{Dn]|nChFjtCvVfmFvF`_Fp{BhkLo@hyB``AjdBxbArrCvQ`{Ev{@rpCj_C`dC~nCheDpaA`aA`xAnfDdf@vv@pfA`zC|z@tnA|~AtO|[haA|k@dx@`}@fW|m@j_Ab~C`vAbaBh}@xXdyAp}Al|@tc@`^zm@uIvmAqDdA|gA~X|WzR_Hnb@evAjuAyB`ThQjbA~w@lHr~@fRvRhg@}F`q@b\\f`AhqAp{AtYnl@vmAx|@je@lr@zPr\\aEtZl]eEzdAtJ|vBqQdjBn_@jqCfz@peHrj@xM|r@nf@|m@rmBxSbpAta@luCp|@z_G"
  },
  "end_addr": "Grand+Junction,+CO",
  "start_addr": "Denver,+CO",
  "status": "OK"
}
```

## Tasks
- [x] configure app to run on gunicorn
- [ ] optimize gunicorn settings for prod
- [ ] fix logging since gunicorn doesn't use logging class
- [ ] set up SSL
- [ ] set up mutual authentication
- [ ] create config file to store API keys
- [ ] create config files for webapp settings (request timeout, port, etc...)
