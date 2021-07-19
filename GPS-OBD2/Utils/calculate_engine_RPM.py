def calculate_engine_RPM(obd_data:dict):
    '''
    This method takes a JSON/Dictionary as input. The PID for engine RPM is 010C. The HEX value is split in two
    namely A and B.
    
    For Example
    
    let,
    OBD_HEX_VALUE = 541B
    
    A = 54(hex) = 84(dec)
    B = 1B(hex) = 27(dec)
    
    Using Formula
    rpm = ( ( A * 256 ) + B ) / 4
    
    Result RPM
    5382.75
    
    '''
    
    # Getting RPM from OBD Data and splitting it into two
    rpm_A = obd_data['010C'][0:2]
    rpm_B = obd_data['010C'][2:]
    
    # Converting Hex to Integer
    converted_decimal_A = int(rpm_A, 16)
    converted_decimal_B = int(rpm_B, 16)
    
    # Formula for conversion to RPM
    RPM = ((converted_decimal_A * 256) + converted_decimal_B)/4
    print(f'Engine RPM {RPM}')
    
    return RPM
