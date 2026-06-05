REGULATIONS_DB = {
    "SOLAS Ch III Reg 20": {
        "title": "Operational readiness, maintenance and inspections",
        "chapter": "SOLAS Chapter III",
        "category": "LSA (Life Saving Appliances)",
        "description": "Requires all life-saving appliances to be in working order and ready for immediate use before the ship leaves port and at all times during the voyage. Mandates weekly and monthly inspections and periodic servicing of launchers and release mechanisms.",
        "checklist_keywords": ["lifeboat", "liferaft", "davit", "release mechanism", "limit switch", "launching", "survival craft"],
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
        "checklist_keywords": ["lifebuoy", "lifejacket", "immersion suit", "reflective tape", "self-igniting light", "battery", "personal life-saving"],
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
        "checklist_keywords": ["fire extinguisher", "fire main", "hydrant", "hose", "nozzle", "co2", "fixed system", "foam", "fire-fighting", "fire detection"],
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
        "checklist_keywords": ["eebd", "escape route", "emergency exit", "signage", "emergency light", "means of escape"],
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
        "checklist_keywords": ["oily water separator", "ows", "15ppm", "bilge", "discharge", "calibration certificate", "filtering equipment", "oil filtering"],
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
        "checklist_keywords": ["compass", "deviation", "magnetic compass", "deviation card", "radar", "ecdis", "gps", "navigational equipment"],
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
        "checklist_keywords": ["epirb", "vhf", "dsc", "radio", "gmdss", "sart", "battery", "telsiz", "telephony"],
        "critical_items": ["epirb", "battery", "expired", "gmdss", "release"],
        "satisfactory_condition": "EPIRB battery and release mechanism within expiry dates, annual test report onboard, DSC alerts tested.",
        "deficiency_action": "Replace expired EPIRB battery/HRU, test DSC communication, verify battery date markings.",
        "applicability": "All Vessels"
    },
    "MARPOL Annex I Reg 6": {
        "title": "IOPP Certificate and Surveys",
        "chapter": "MARPOL Annex I",
        "category": "Documentation",
        "description": "Requires ships of 400 GT and above to keep a valid International Oil Pollution Prevention (IOPP) Certificate, verifying compliance with oil pollution standards.",
        "checklist_keywords": ["iopp", "oil pollution", "pollution prevention certificate", "prevention of oil pollution"],
        "critical_items": ["iopp", "expired", "missing", "certificate"],
        "satisfactory_condition": "IOPP Certificate is valid and available onboard.",
        "deficiency_action": "Renew or update IOPP certificate, schedule immediate class survey.",
        "applicability": "All Vessels >= 400 GT"
    },
    "SOLAS Ch I Reg 12": {
        "title": "Safety Certificates (Construction, Equipment, Radio)",
        "chapter": "SOLAS Chapter I",
        "category": "Documentation",
        "description": "Mandates the carriage of Cargo Ship Safety Construction, Safety Equipment, and Safety Radio Certificates confirming compliance with safety parameters.",
        "checklist_keywords": ["safety construction", "safety equipment certificate", "safety radio certificate", "safcon", "safel", "safrad", "safetysigns", "exemptions"],
        "critical_items": ["expired", "missing", "invalid"],
        "satisfactory_condition": "All SOLAS Safety Certificates are valid, endorsed, and kept onboard.",
        "deficiency_action": "Liaise with classification society / flag administration to arrange surveys and reissue/renew certificates.",
        "applicability": "All Vessels"
    },
    "MARPOL Annex VI Reg 6": {
        "title": "IAPP Certificate (Air Pollution Prevention)",
        "chapter": "MARPOL Annex VI",
        "category": "Documentation",
        "description": "Requires ships of 400 GT and above to carry a valid International Air Pollution Prevention (IAPP) Certificate verifying compliance with SOx/NOx emission limits.",
        "checklist_keywords": ["iapp", "air pollution", "exhaust gas", "emission", "air pollution prevention"],
        "critical_items": ["iapp", "expired", "missing"],
        "satisfactory_condition": "IAPP certificate is valid and onboard; exhaust logs and fuel delivery notes maintained.",
        "deficiency_action": "Obtain valid IAPP certificate; verify compliance of engines/fuel records.",
        "applicability": "All Vessels >= 400 GT"
    },
    "SOLAS Ch II-1": {
        "title": "Structure, machinery and electrical installations",
        "chapter": "SOLAS Chapter II-1",
        "category": "Machinery & Hull",
        "description": "Sets structural, watertight, machinery, and electrical backup standards for vessels to ensure general ship survivability.",
        "checklist_keywords": ["machinery", "bilge pump", "electrical installation", "generator", "watertight door", "steering gear", "rudder", "shaft"],
        "critical_items": ["bilge pump", "generator", "steering gear", "watertight"],
        "satisfactory_condition": "Bilge pumping system, emergency generator, steering gear, and watertight seals are fully functional and tested.",
        "deficiency_action": "Repair or overhaul failing machinery/steering components; verify backup power systems.",
        "applicability": "All Vessels"
    },
    "BWM D-2": {
        "title": "Ballast Water Performance Standard & Record Book",
        "chapter": "BWM Convention",
        "category": "Environmental / Pollution",
        "description": "Requires ships to manage ballast water to meet biological standards (D-2) and maintain a Ballast Water Record Book. Also complies with MEPC BWM guidelines.",
        "checklist_keywords": ["ballast", "bwm", "ballast water", "ballast record book", "treatment system", "bwms", "mepc ballast"],
        "critical_items": ["bwms", "treatment", "record book", "expired"],
        "satisfactory_condition": "Ballast Water Management System (BWMS) functional, active substance log maintained, Ballast Water Record Book updated and signed.",
        "deficiency_action": "Service Ballast Water Treatment System, replace filters, update Ballast Water Record Book entries.",
        "applicability": "All Vessels"
    },
    "AFS Convention": {
        "title": "Control of Harmful Anti-fouling Systems",
        "chapter": "AFS Convention",
        "category": "Environmental / Pollution",
        "description": "Prohibits the use of harmful organotin compounds in anti-fouling paints. Requires an International Anti-fouling System Certificate or Declaration.",
        "checklist_keywords": ["anti-fouling", "afs", "organotin", "paint", "tbt", "declaration of anti-fouling", "afc paint"],
        "critical_items": ["organotin", "tbt", "afs", "certificate"],
        "satisfactory_condition": "Organotin-free anti-fouling coating applied, International Anti-fouling System Certificate or Declaration available onboard.",
        "deficiency_action": "Provide organotin-free statement from paint manufacturer, plan hull recoating if non-compliant paint detected.",
        "applicability": "All Vessels"
    },
    "MARPOL Annex IV Reg 9": {
        "title": "Sewage systems and discharge connections",
        "chapter": "MARPOL Annex IV",
        "category": "Environmental / Pollution",
        "description": "Specifies sewage treatment plants, disinfecting systems, holding tanks, and standard discharge connection flanges.",
        "checklist_keywords": ["sewage", "sewage treatment", "holding tank", "macerator", "disinfection", "toilet"],
        "critical_items": ["treatment plant", "macerator", "disinfection", "leak"],
        "satisfactory_condition": "Sewage treatment plant functioning, chemical disinfection records maintained, standard discharge connection flange available.",
        "deficiency_action": "Service sewage treatment plant aeration system, replenish chemical dosing, clean holding tank level indicators.",
        "applicability": "All Vessels >= 400 GT"
    },
    "MARPOL Annex V Reg 10": {
        "title": "Placards, garbage management plans and record keeping",
        "chapter": "MARPOL Annex V",
        "category": "Environmental / Pollution",
        "description": "Requires placards for ships of 12m or more, a Garbage Management Plan for ships of 100 GT and above, and a Garbage Record Book for ships of 400 GT and above.",
        "checklist_keywords": ["garbage", "garbage record book", "garbage management plan", "placard", "waste", "food waste", "plastics"],
        "critical_items": ["garbage record book", "plan", "placard", "missing"],
        "satisfactory_condition": "Garbage Record Book signed up-to-date, Garbage Management Plan implemented, placards displayed in crew languages.",
        "deficiency_action": "Display missing garbage placards, update Garbage Record Book entries, replenish recycling/waste receptacles.",
        "applicability": "All Vessels"
    },
    "ICLL Art 12": {
        "title": "Load Line Certificate and marking of draft marks",
        "chapter": "Load Line Convention",
        "category": "Draft & Integrity",
        "description": "Regulates draft marks, load line marks (Plimsoll line), deck line, and freeing ports to ensure adequate reserve buoyancy.",
        "checklist_keywords": ["load line", "draft mark", "plimsoll", "freeboard", "deck line", "freeing port", "overload"],
        "critical_items": ["load line", "draft mark", "corroded", "illegible"],
        "satisfactory_condition": "Load line and draft marks clearly visible, welded and painted, freeing port flaps moving freely.",
        "deficiency_action": "Repaint weathered draft and load line markings, free stuck freeing port flaps, restore seals on deck openings.",
        "applicability": "All Vessels"
    },
    "AFS Certificate": {
        "title": "International Anti-Fouling System Certificate",
        "chapter": "AFS Convention",
        "category": "Documentation",
        "description": "Mandates ships of 400 GT and above to carry the International Anti-Fouling System Certificate.",
        "checklist_keywords": ["afs certificate", "anti-fouling certificate", "declaration on anti-fouling", "afc certificate"],
        "critical_items": ["expired", "missing", "invalid"],
        "satisfactory_condition": "Valid AFS certificate or Declaration of AFS available onboard.",
        "deficiency_action": "Request survey from Class to reissue AFS certificate, ensure proper documentation of applied paint systems.",
        "applicability": "All Vessels >= 400 GT"
    },
    "BWM Certificate": {
        "title": "International Ballast Water Management Certificate",
        "chapter": "BWM Convention",
        "category": "Documentation",
        "description": "Requires ships of 400 GT and above to carry a Ballast Water Management Certificate and an approved BWM Plan.",
        "checklist_keywords": ["bwm certificate", "ballast water certificate", "ballast water management plan", "bwmp"],
        "critical_items": ["expired", "missing", "invalid"],
        "satisfactory_condition": "Valid BWM Certificate and approved Ballast Water Management Plan available onboard.",
        "deficiency_action": "Liaise with Class to survey BWMS and issue certificate, update BWM plan to current regulations.",
        "applicability": "All Vessels >= 400 GT"
    },
    "SOLAS Ch III Reg 35": {
        "title": "Training manual and onboard training aids",
        "chapter": "SOLAS Chapter III",
        "category": "LSA (Life Saving Appliances)",
        "description": "Requires a training manual to be provided in each crew mess room and recreation room or in each crew cabin. It must contain instructions and information on the life-saving appliances provided in the ship.",
        "checklist_keywords": ["training manual", "solas training manual", "eğitim el kitabı", "training aids"],
        "critical_items": ["training manual"],
        "satisfactory_condition": "Training manual available in crew mess/cabins, containing up-to-date instructions.",
        "deficiency_action": "Provide or update the SOLAS training manual on board in appropriate crew spaces.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch III Reg 36": {
        "title": "Instructions for onboard maintenance",
        "chapter": "SOLAS Chapter III",
        "category": "LSA (Life Saving Appliances)",
        "description": "Requires instructions for onboard maintenance of life-saving appliances to be provided and maintenance to be carried out accordingly.",
        "checklist_keywords": ["maintenance instructions", "lsa maintenance manual", "bakım talimatları", "onboard maintenance"],
        "critical_items": ["maintenance instructions"],
        "satisfactory_condition": "Maintenance manuals available, weekly/monthly checks documented.",
        "deficiency_action": "Implement LSA maintenance logbook and provide instructions on board.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch III Reg 19": {
        "title": "Emergency training and drills",
        "chapter": "SOLAS Chapter III",
        "category": "LSA (Life Saving Appliances)",
        "description": "Mandates monthly abandon ship and fire drills. Requires records of drills to be maintained in the official logbook.",
        "checklist_keywords": ["abandon ship drill", "fire drill", "drill records", "yangın talimi", "talim kayıtları", "abandon ship", "muster list drill"],
        "critical_items": ["drill", "drill record"],
        "satisfactory_condition": "Abandon ship and fire drills conducted monthly, records maintained in logbook.",
        "deficiency_action": "Conduct required drills under surveyor observation and record in logbook.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch III Reg 8": {
        "title": "Muster list and emergency instructions",
        "chapter": "SOLAS Chapter III",
        "category": "LSA (Life Saving Appliances)",
        "description": "Requires clear instructions to be provided for every person on board, to be followed in the event of an emergency. Muster lists must be exhibited in conspicuous places.",
        "checklist_keywords": ["muster list", "emergency instructions", "role table", "görev cetveli", "acil durum talimatı"],
        "critical_items": ["muster list"],
        "satisfactory_condition": "Muster lists posted in conspicuous places, showing duties of crew members.",
        "deficiency_action": "Update and post muster lists at bridge, engine room, and accommodation spaces.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch V Reg 23": {
        "title": "Pilot transfer arrangements",
        "chapter": "SOLAS Chapter V",
        "category": "Navigation",
        "description": "Specifies requirements for pilot ladders, accommodation ladders, and associated equipment to ensure safe transfer of pilots.",
        "checklist_keywords": ["pilot ladder", "pilot transfer", "accommodation ladder", "klavuz çarmıhı", "pilot ladder certificate", "pilot hoist"],
        "critical_items": ["pilot ladder", "shackle", "step"],
        "satisfactory_condition": "Pilot ladder clean, steps in good condition, certificated manropes, warning signs posted.",
        "deficiency_action": "Replace worn steps or ropes, use certified pilot ladder, ensure proper securing.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch II-1 Reg 13-1": {
        "title": "Openings in watertight bulkheads and internal doors",
        "chapter": "SOLAS Chapter II-1",
        "category": "Machinery & Hull",
        "description": "Requires watertight doors in passenger and cargo ships to be kept closed during navigation, except when authorized. Requires daily testing.",
        "checklist_keywords": ["watertight door", "internal door", "su geçirmez kapı", "bulkhead door", "watertight bulkheads"],
        "critical_items": ["watertight", "seal", "gasket"],
        "satisfactory_condition": "Watertight door seals intact, local/remote alarms and indicators operational.",
        "deficiency_action": "Replace damaged rubber gaskets, adjust door locking mechanism, test remote indication.",
        "applicability": "All Vessels"
    },
    "SOLAS Ch II-1 Reg 29": {
        "title": "Steering gear",
        "chapter": "SOLAS Chapter II-1",
        "category": "Machinery & Hull",
        "description": "Requires main and auxiliary steering gears to be tested within 12 hours before departure. Specifies performance and redundancy standards.",
        "checklist_keywords": ["steering gear", "rudder carrier", "dümen makinesi", "telemetric", "hydraulic steering"],
        "critical_items": ["steering gear", "oil leak", "auxiliary steering"],
        "satisfactory_condition": "Main and auxiliary steering systems fully operational, no hydraulic leaks, alarm tests passed.",
        "deficiency_action": "Repair hydraulic pump leaks, top up oil levels, verify auxiliary steering time limit compliance.",
        "applicability": "All Vessels"
    },
    "ILO 152": {
        "title": "Occupational Safety and Health (Dock Work) Convention (Cargo Gear)",
        "chapter": "ILO Convention 152",
        "category": "Machinery & Hull",
        "description": "Requires lifting appliances and loose gear to be tested and examined periodically, with records kept in the Register of Lifting Appliances (Cargo Gear Booklet).",
        "checklist_keywords": ["cargo gear", "lifting appliance", "crane", "winch", "loose gear", "cargo gear booklet", "derrick", "wire rope certificate"],
        "critical_items": ["crane", "cargo gear booklet", "wire rope", "loose gear"],
        "satisfactory_condition": "Register of Lifting Appliances updated, annual examination completed, wires within wear limits.",
        "deficiency_action": "Renew hoisting/luffing wire ropes, service crane limit switches, update Cargo Gear Register.",
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
