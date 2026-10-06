from fastapi import APIRouter
from src.schemas import EVMRequest, EVMResponse
from src.evm import calculate_cpi, calculate_spi, calculate_eac, calculate_tcpi, interpret_cpi, interpret_spi

router = APIRouter(prefix="/evm", tags=["EVM"])

@router.post("", response_model=EVMResponse)
def calculate_evm(request: EVMRequest):
    cpi = calculate_cpi(request.EV, request.AC)
    spi = calculate_spi(request.EV, request.PV)
    eac = calculate_eac(request.BAC, cpi)
    tcpi = calculate_tcpi(request.BAC, request.EV, request.AC)
    
    return EVMResponse(
        PV=request.PV,
        EV=request.EV,
        AC=request.AC,
        CPI=cpi,
        SPI=spi,
        EAC=eac,
        TCPI=tcpi,
        cpi_interpretation=interpret_cpi(cpi),
        spi_interpretation=interpret_spi(spi)
    )
