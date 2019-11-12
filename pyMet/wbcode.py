
from enum import IntFlag, auto

def DataTypeToDict():
	return {i.value: i.name for i in DataType}

class DataType(IntFlag):
    # version 0001
	Temperature = auto()
	MaxDailyT = auto()
	MinDailyT = auto()
	Precipitation = auto()
	Rainfall = auto()
	Snowfall = auto()
	Snowdepth = auto()
	SnowpackSWE = auto()
	SnowMelt = auto()
	AtmosphericYield = auto()
	AtmosphericDemand = auto()
	Radiation = auto()
	RadiationSW = auto()
	RadiationLW = auto()
	CloudCover = auto()
	RH = auto()
	AtmosphericPressure = auto()
	Windspeed = auto()
	Windgust = auto()
	WindDirection = auto()
	HeatDegreeDays = auto()
	CoolDegreeDays = auto()
	Unspecified23 = auto()
	HeadStage = auto()
	Flux = auto()
	UnitDischarge = auto()
	Unspecified27 = auto()
	Unspecified28 = auto()
	Unspecified29 = auto()
	Unspecified30 = auto()
	Storage = auto()
	SnowPackCover = auto()
	SnowPackLWC = auto()
	SnowPackAlbedo = auto()
	SnowSurfaceTemp = auto()
	Unspecified36 = auto()
	Unspecified37 = auto()
	DepressionWaterContent = auto()
	InterceptionWaterContent = auto()
	SoilSurfaceTemp = auto()
	SoilSurfaceRH = auto()
	SoilMoistureContent = auto()
	SoilMoisturePressure = auto()
	Unspecified44 = auto()
	Unspecified45 = auto()
	Unspecified46 = auto()
	Unspecified47 = auto()
	Evaporation = auto()
	Transpiration = auto()
	Evapotranspiration = auto()
	Infiltration = auto()
	Runoff = auto()
	Recharge = auto()
	TotalHead = auto()
	PressureHead = auto()
	SubSurfaceLateralFlux = auto()
	FluxLeft = auto()
	FluxRight = auto()
	FluxFront = auto()
	FluxBack = auto()
	FluxBottom = auto()
	FluxTop = auto()
	OutgoingRadiationLW = auto()
	Reserved = auto()

class WaterBalanceDataCode:
    wbc = 0
    dts = []

    def __init__(self,datatypes=None):
        if datatypes is None: return	
        if type(datatypes)==DataType:
            self.wbc = int(datatypes)
            self.dts = [dtc.name for dtc in DataType if int(datatypes) & dtc]
        elif type(datatypes)==int:
            self.wbc = datatypes
            self.dts = [dtc.name for dtc in DataType if datatypes & dtc]
        elif type(datatypes)==list:
            wbc=0
            for dt in datatypes:
                if type(dt)==str:
                    wbc+=DataType[dt].value
                else:
                    wbc+=dt
            self.__init__(wbc)
        elif type(datatypes)==str:
            try:
                self.__init__(DataType[datatypes].value)
            except:
                print('unrecognized WaterBalanceDataCode name:',datatypes)
        else:
            print('unknown WaterBalanceDataCode input type: ' + str(type(datatypes)))