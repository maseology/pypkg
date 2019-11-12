Public Class WaterBalanceDataCode

    Enum DataType
        Temperature
        MaxDailyT
        MinDailyT
        Precipitation
        Rainfall
        Snowfall
        Snowdepth
        SnowpackSWE
        SnowMelt
        AtmosphericYield
        AtmosphericDemand
        Radiation
        RadiationSW
        RadiationLW
        CloudCover
        RH
        AtmosphericPressure
        Windspeed
        Windgust
        WindDirection
        HeatDegreeDays
        CoolDegreeDays
        Unspecified23
        HeadStage
        Flux
        UnitDischarge
        Unspecified27
        Unspecified28
        Unspecified29
        Unspecified30
        Storage
        SnowPackCover
        SnowPackLWC
        SnowPackAlbedo
        SnowSurfaceTemp
        Unspecified36
        Unspecified37
        DepressionWaterContent
        InterceptionWaterContent
        SoilSurfaceTemp
        SoilSurfaceRH
        SoilMoistureContent
        SoilMoisturePressure
        Unspecified44
        Unspecified45
        Unspecified46
        Unspecified47
        Evaporation
        Transpiration
        Evapotranspiration
        Infiltration
        Runoff
        Recharge
        TotalHead
        PressureHead
        SubSurfaceLateralFlux
        FluxLeft
        FluxRight
        FluxFront
        FluxBack
        FluxBottom
        FluxTop
        OutgoingRadiationLW
        Reserved
    End Enum

    Private _dts As List(Of DataType)
    Public ReadOnly Property DataTypesCode() As ULong
        Get
            Dim ul1 As ULong = 0
            For Each dt In _dts
                ul1 += 2 ^ dt
            Next
            Return ul1
        End Get
    End Property
    Public ReadOnly Property DataTypeList As List(Of DataType)
        Get
            Return _dts
        End Get
    End Property

    Sub New()
    End Sub
    Sub New(DataTypesCode As ULong)
        _dts = LoadDTC(DataTypesCode)
    End Sub

    Private Shared Function LoadDTC(DataTypesCode As ULong) As List(Of DataType)
        Dim lstOUT As New List(Of DataType)
        Dim ch1() As Char = mmIO.IntegerToBinary(DataTypesCode).ToCharArray.Reverse.ToArray
        For i As Integer = 0 To ch1.Length - 1 Step 1
            If ch1(i) = "1"c Then
                lstOUT.Add(i)
            End If
        Next i
        Return lstOUT
    End Function
    Sub AddDataType(DT As DataType)
        If IsNothing(_dts) Then _dts = New List(Of DataType)
        If Not _dts.Contains(DT) Then _dts.Add(DT)
    End Sub

    Sub WriteToBinary(bw As BinaryWriter, MeasurementDate As Date, DataIN As Dictionary(Of Integer, Double))
        With bw
            .Write(MeasurementDate.ToBinary)
            For i = 0 To 63
                If DataIN.ContainsKey(i) Then .Write(DataIN(i))
            Next
        End With
    End Sub
    Sub WriteToBinary(bw As BinaryWriter, DataIN As Dictionary(Of Integer, Double))
        With bw
            For i = 0 To 63
                If DataIN.ContainsKey(i) Then .Write(DataIN(i))
            Next
        End With
    End Sub

    Shared Function ReadFromBinary(br As BinaryReader, DataTypesCode As ULong) As SortedDictionary(Of Date, Dictionary(Of DataType, Double))
        Dim dicOUT As New SortedDictionary(Of Date, Dictionary(Of DataType, Double)), DTC = LoadDTC(DataTypesCode)
        With br
100:        Dim dt1 = Date.FromBinary(.ReadInt64), dicC As New Dictionary(Of DataType, Double)
            For Each t In DTC
                dicC.Add(t, .ReadDouble)
            Next
            dicOUT.Add(dt1, dicC)
            If .PeekChar <> -1 Then GoTo 100
        End With
        Return dicOUT
    End Function
    Shared Function ReadFromBinary_single_step(br As BinaryReader, DataTypesCode As ULong) As Dictionary(Of DataType, Double)
        Dim dicC As New Dictionary(Of DataType, Double)
        For Each t In LoadDTC(DataTypesCode)
            dicC.Add(t, br.ReadDouble)
        Next
        Return dicC
    End Function

End Class