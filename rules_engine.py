REGULATIONS_DB = {
    "SOLAS Ch III Reg 20": {
        "title": "Operational readiness, maintenance and inspections",
        "chapter": "SOLAS Chapter III",
        "category": "LSA (Life Saving Appliances)",
        "description": "Requires all life-saving appliances to be in working order and ready for immediate use before the ship leaves port and at all times during the voyage. Mandates weekly and monthly inspections and periodic servicing of launchers and release mechanisms.",
        "checklist_keywords": ["lifeboat", "liferaft", "davit", "release mechanism", "limit switch", "launching"],
        "critical_items": ["release mechanism", "limit switch", "hydrostatic release unit", "hru"],
        "satisfactory_condition": "Release mechanisms clean, limit switches tested and operational, no corrosion, service within date.",
        "deficiency_action": "Clean and lubricate mechanisms, replace/repair corroded limit switches, re-test under survey observation.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch III Reg 7": {
        "title": "Personal life-saving appliances",
        "chapter": "SOLAS Chapter III",
        "category": "LSA (Life Saving Appliances)",
        "description": "Specifies requirements for lifebuoys (retro-reflective tape, self-igniting lights, buoyant lifelines), lifejackets, and immersion suits, ensuring correct numbering, placement, and visual condition.",
        "checklist_keywords": ["lifebuoy", "lifejacket", "immersion suit", "reflective tape", "self-igniting light", "battery"],
        "critical_items": ["reflective tape", "battery", "light", "expire"],
        "satisfactory_condition": "Retro-reflective tape properly adhered, batteries within validity, whistles attached, correct markings.",
        "deficiency_action": "Apply marine-grade retro-reflective tape, replace expired batteries/lights, replenish missing inventory.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch II-2 Reg 10": {
        "title": "Fire fighting and fire extinguishing systems",
        "chapter": "SOLAS Chapter II-2",
        "category": "FFE (Fire Fighting Equipment)",
        "description": "Regulates fire mains, hydrants, hoses, nozzles, and portable/fixed fire extinguishing systems. Requires annual servicing, inspection, hydrostatic testing, and pressure testing of main lines.",
        "checklist_keywords": ["fire extinguisher", "fire main", "hydrant", "hose", "nozzle", "co2", "fixed system", "foam"],
        "critical_items": ["extinguisher", "service", "pressure", "hydrostatic", "overdue"],
        "satisfactory_condition": "Extinguishers serviced within 12 months, pressure gauges in green zone, lines free of leaks, couplers working.",
        "deficiency_action": "Send extinguishers to shore-approved station for servicing, replace leaking valves, perform pressure test.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch II-2 Reg 13": {
        "title": "Means of escape",
        "chapter": "SOLAS Chapter II-2",
        "category": "Fire Safety",
        "description": "Prescribes escape routes, emergency lighting, signage, and Emergency Escape Breathing Devices (EEBD). EEBDs must be inspected, fully charged, and placed in designated locations (engine room, accommodation).",
        "checklist_keywords": ["eebd", "escape route", "emergency exit", "signage", "emergency light"],
        "critical_items": ["eebd", "pressure", "charge", "exit", "obstructed"],
        "satisfactory_condition": "EEBD pressure indicators within limits, escape routes clear of obstructions, signage photo-luminescent.",
        "deficiency_action": "Recharge or replace low-pressure EEBDs, clear all escape routes, repair emergency exit lighting.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch II-2 Reg 4": {
        "title": "Probability of ignition (Pump Rooms & Oil Piping)",
        "chapter": "SOLAS Chapter II-2",
        "category": "Fire Safety",
        "description": "Controls fuel oil arrangements, ventilation, and safety equipment in cargo pump rooms to prevent explosions. Requires temperature sensors, gas detection, and bilge alarms.",
        "checklist_keywords": ["pump room", "gas detection", "bilge alarm", "ventilation shutdown", "temperature sensor"],
        "critical_items": ["gas detection", "sensor", "ventilation"],
        "satisfactory_condition": "Gas detection system calibrated, pump bearings temperature monitors functional, bilge alarm operational.",
        "deficiency_action": "Calibrate gas sensor, repair/replace temperature monitors, test pump room bilge level switches.",
        "applicability": "Tankers Only"
    },
    "MARPOL Annex I Reg 14": {
        "title": "Oil filtering equipment (Oily Water Separator)",
        "chapter": "MARPOL Annex I",
        "category": "Environmental / Pollution",
        "description": "Requires any ship of 400 gross tonnage and above to be fitted with oil filtering equipment (OWS) that ensures bilge discharges do not exceed 15 ppm. Mandates automatic shutdown and calibration of 15 ppm alarm monitor.",
        "checklist_keywords": ["oily water separator", "ows", "15ppm", "bilge", "discharge", "calibration certificate"],
        "critical_items": ["15ppm", "calibration", "ows", "certificate", "expired"],
        "satisfactory_condition": "OWS operational, 15 ppm monitor calibration certificate within 5-year limit (or annual check valid), automatic recirculating valve working.",
        "deficiency_action": "Recalibrate 15 ppm sensor, obtain class-approved certificate, service separating coalescer elements.",
        "applicability": "All Vessels >= 400 GT"
    },
    "MARPOL Annex I Reg 17": {
        "title": "Oil Record Book Part I (Machinery space operations)",
        "chapter": "MARPOL Annex I",
        "category": "Documentation",
        "description": "Mandates maintaining an Oil Record Book Part I for machinery spaces to record operations including bilge discharges, oil transfer, disposal of sludge, and cleaning of tanks.",
        "checklist_keywords": ["oil record book", "orb", "machinery space", "bilge discharge", "sludge tank", "entry", "log"],
        "critical_items": ["entry", "signature", "discrepancy", "missing"],
        "satisfactory_condition": "Entries updated page-by-page, signed by chief engineer and master, tank volumes match actual levels.",
        "deficiency_action": "Correct entries with formal strikethrough and master sign-off, update bilge holding records.",
        "applicability": "All Vessels >= 400 GT"
    },
    "SOLAS Ch V Reg 19": {
        "title": "Shipborne navigational equipment",
        "chapter": "SOLAS Chapter V",
        "category": "Navigation",
        "description": "Requires a magnetic compass properly adjusted with a deviation card, plus GPS, AIS, ECDIS, and radar installations depending on gross tonnage.",
        "checklist_keywords": ["compass", "deviation", "magnetic compass", "deviation card", "radar", "ecdis", "gps"],
        "critical_items": ["deviation card", "compass", "calibration", "outdated"],
        "satisfactory_condition": "Magnetic compass bubble-free, deviation table updated annually or after maintenance, deviation within 3 degrees.",
        "deficiency_action": "Adjust magnetic compass by certified adjuster, issue new deviation card, top up compass fluid.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch IV Reg 7": {
        "title": "Radio equipment - General and EPIRB",
        "chapter": "SOLAS Chapter IV",
        "category": "Radio / GMDSS",
        "description": "Specifies GMDSS radio equipment including VHF, MF/HF, SART, and EPIRBs. EPIRBs must be tested annually and have valid batteries and hydrostatic release mechanisms.",
        "checklist_keywords": ["epirb", "vhf", "dsc", "radio", "gmdss", "sart", "battery"],
        "critical_items": ["epirb", "battery", "expired", "gmdss", "release"],
        "satisfactory_condition": "EPIRB battery and release mechanism within expiry dates, annual test report onboard, DSC alerts tested.",
        "deficiency_action": "Replace expired EPIRB battery/HRU, test DSC communication, verify battery date markings.",
        "applicability": "All Vessels"
    }
}

def get_rule_by_keyword(text):
    text_lower = text.lower()
    best_match = None
    max_matches = 0
    for rule_code, rule_info in REGULATIONS_DB.items():
        matches = sum(1 for keyword in rule_info["checklist_keywords"] if keyword in text_lower)
        if matches > max_matches:
            max_matches = matches
            best_match = rule_code
    return best_match if max_matches > 0 else "N/A"

def check_rule_applicability(rule_code, vessel_type, grt):
    if rule_code not in REGULATIONS_DB:
        return True, "Kural tanımlanmamış."
        
    rule = REGULATIONS_DB[rule_code]
    app = rule["applicability"]
    
    if app == "All Vessels":
        return True, "Tüm gemiler için zorunludur."
    if app == "Tankers Only":
        if "Tanker" in vessel_type or "Tankeri" in vessel_type:
            return True, f"Tanker sınıfı ({vessel_type}) gemiler için zorunludur."
        else:
            return False, f"Bu kural tankerlere özeldir, {vessel_type} sınıfı için geçerli değildir."
    if ">= 400 GT" in app:
        try:
            if isinstance(grt, str):
                grt_clean = int(grt.replace(",", "").replace(".", "").split()[0])
            else:
                grt_clean = int(grt)
        except Exception:
            grt_clean = 500
            
        if grt_clean >= 400:
            return True, f"400 GT ve üzeri gemiler için zorunludur (Gemi GRT: {grt_clean})."
        else:
            return False, f"Gemi tonajı 400 GT altındadır ({grt_clean} GT). Bu kural geçerli olmayabilir."
    return True, "Genel uygulama."
