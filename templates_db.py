import json
import os
import re

STATIC_TEMPLATES = {
    "ANNEX I IOPP (Oil Pollution Prevention)": [
        {"id": "IOPP-01", "item": "Oily Water Separator (OWS) 15 ppm alarm and automatic stopping device tested and found fully functional.", "rule": "MARPOL Annex I Reg 14", "default_status": "Y"},
        {"id": "IOPP-02", "item": "Oil Record Book Part I updated, page-by-page signed by Chief Engineer & Master, matching engine room log tank levels.", "rule": "MARPOL Annex I Reg 17", "default_status": "Y"},
        {"id": "IOPP-03", "item": "Standard discharge connection provided and in good visual condition.", "rule": "MARPOL Annex I Reg 13", "default_status": "Y"},
        {"id": "IOPP-04", "item": "Sludge and bilge holding tanks capacity matches capacity listed in IOPP Certificate Form A/B.", "rule": "MARPOL Annex I Reg 12", "default_status": "Y"},
        {"id": "IOPP-05", "item": "No unauthorized bypass lines or piping modifications observed in bilge/sludge transfer lines.", "rule": "MARPOL Annex I Reg 14", "default_status": "Y"}
    ],
    "ANNEX IV SPP (Sewage Pollution Prevention)": [
        {"id": "ISPP-01", "item": "Sewage treatment plant operational, biological media active, and air blower functional.", "rule": "MARPOL Annex IV Reg 9", "default_status": "Y"},
        {"id": "ISPP-02", "item": "Sewage comminuting and disinfecting system working, disinfection chemical levels sufficient.", "rule": "MARPOL Annex IV Reg 9", "default_status": "Y"},
        {"id": "ISPP-03", "item": "Sewage holding tank structural integrity, high-level alarms, and level indicators tested.", "rule": "MARPOL Annex IV Reg 9", "default_status": "Y"},
        {"id": "ISPP-04", "item": "Standard discharge flange and piping connection in good working order with no leaks.", "rule": "MARPOL Annex IV Reg 10", "default_status": "Y"},
        {"id": "ISPP-05", "item": "Sewage discharge rate control matches approvals and ship speed restrictions.", "rule": "MARPOL Annex IV Reg 11", "default_status": "Y"}
    ],
    "ANNEX VI IAPPC (Air Pollution Prevention)": [
        {"id": "IAPPC-01", "item": "Incinerator operational, temperature controllers, gas emission levels, and safety shutdowns functional.", "rule": "MARPOL Annex VI Reg 16", "default_status": "Y"},
        {"id": "IAPPC-02", "item": "Fuel oil changeover logbook maintained, sulphur content checked (<= 0.50% or 0.10% in ECA).", "rule": "MARPOL Annex VI Reg 14", "default_status": "Y"},
        {"id": "IAPPC-03", "item": "Ozone-depleting substances record book maintained, equipment containing ODS leak-free.", "rule": "MARPOL Annex VI Reg 12", "default_status": "Y"},
        {"id": "IAPPC-04", "item": "EIAPP Certificates for diesel engines onboard, NOX technical files complete and available.", "rule": "MARPOL Annex VI Reg 13", "default_status": "Y"},
        {"id": "IAPPC-05", "item": "Exhaust Gas Cleaning System (EGCS/Scrubber) pH sensors, pressure gauges, and alarms calibrated.", "rule": "MARPOL Annex VI Reg 14", "default_status": "Y"}
    ],
    "BWM (Ballast Water Management)": [
        {"id": "BWM-01", "item": "Approved Ballast Water Management Plan (BWMP) onboard, implemented, and crew trained.", "rule": "BWM D-2", "default_status": "Y"},
        {"id": "BWM-02", "item": "Ballast Water Record Book (BWRB) updated, entries signed page-by-page by officers.", "rule": "BWM D-2", "default_status": "Y"},
        {"id": "BWM-03", "item": "Ballast Water Management System (BWMS) filters, UV lamps/electrolysis cells, and flow meters operational.", "rule": "BWM D-2", "default_status": "Y"},
        {"id": "BWM-04", "item": "BWMS calibration certificates within validity, logs printout and storage functional.", "rule": "BWM D-2", "default_status": "Y"},
        {"id": "BWM-05", "item": "Crew trained in BWM operations, safety checklist for active substances complete.", "rule": "BWM D-2", "default_status": "Y"}
    ],
    "LL (International Load Line)": [
        {"id": "LL-01", "item": "Hatch covers, coamings, securing toggles, and gaskets watertight and structurally sound.", "rule": "ICLL Reg 16", "default_status": "Y"},
        {"id": "LL-02", "item": "Cargo ports, bow/stern doors, side scuttles, and deadlights watertight and closing properly.", "rule": "ICLL Reg 10", "default_status": "Y"},
        {"id": "LL-03", "item": "Ventilators, air pipes, automatic float valves in good condition, seals checked.", "rule": "ICLL Reg 18", "default_status": "Y"},
        {"id": "LL-04", "item": "Freeboard marks and load lines permanent, clearly painted, and matching certificate.", "rule": "ICLL Reg 5", "default_status": "Y"},
        {"id": "LL-05", "item": "Guard rails, bulwarks, gangways, and freeing ports in structurally sound condition.", "rule": "ICLL Reg 25", "default_status": "Y"}
    ],
    "SE (Safety Equipment)": [
        {"id": "1.1", "item": "Lifeboats and davits in operational readiness, limit switches tested, launching release mechanisms lubed.", "rule": "SOLAS Ch III Reg 20", "default_status": "Y"},
        {"id": "1.2", "item": "Fire mains, pumps, hydrants, hoses, and nozzles in good condition, pressure tested with no leaks.", "rule": "SOLAS Ch II-2 Reg 10", "default_status": "Y"},
        {"id": "1.3", "item": "Fixed fire extinguishing system (CO2/Foam) cylinders weight/pressure checked, release lines free.", "rule": "SOLAS Ch II-2 Reg 10", "default_status": "Y"},
        {"id": "1.4", "item": "Lifebuoys, lifejackets, and immersion suits check: retro-reflective tapes, lights, and batteries valid.", "rule": "SOLAS Ch III Reg 7", "default_status": "Y"},
        {"id": "1.5", "item": "Emergency Escape Breathing Devices (EEBD) pressure indicator in green zone, correct placement.", "rule": "SOLAS Ch II-2 Reg 13", "default_status": "Y"}
    ],
    "SC (Safety Construction)": [
        {"id": "1.1", "item": "Structural integrity of shell plating, framing, and bulkheads visually checked and free of severe corrosion.", "rule": "SOLAS Ch II-1", "default_status": "Y"},
        {"id": "1.2", "item": "Watertight doors test: local and remote control panel indicator lights and alarms functional.", "rule": "SOLAS Ch II-1 Reg 21", "default_status": "Y"},
        {"id": "1.3", "item": "Engine room ventilation dampers and remote fuel oil quick-closing valves tested.", "rule": "SOLAS Ch II-2 Reg 5", "default_status": "Y"},
        {"id": "1.4", "item": "Bilge pumping arrangement in machinery space and bilge high-level alarms functional.", "rule": "SOLAS Ch II-1", "default_status": "Y"},
        {"id": "1.5", "item": "Windlass and anchoring equipment checked: brakes, clenches, and emergency release working.", "rule": "SOLAS Ch II-1", "default_status": "Y"}
    ],
    "SR (Safety Radio)": [
        {"id": "1.1", "item": "VHF/DSC and MF/HF radio communication tested on reserve source of energy.", "rule": "SOLAS Ch IV Reg 7", "default_status": "Y"},
        {"id": "1.2", "item": "EPIRB annual test report onboard, battery and hydrostatic release mechanism valid.", "rule": "SOLAS Ch IV Reg 7", "default_status": "Y"},
        {"id": "1.3", "item": "GMDSS reserve batteries checked: voltage and specific gravity within normal values.", "rule": "SOLAS Ch IV", "default_status": "Y"},
        {"id": "1.4", "item": "GMDSS radio logbook completed, DSC daily/weekly test entries recorded.", "rule": "SOLAS Ch IV", "default_status": "Y"},
        {"id": "1.5", "item": "Search and Rescue Transponders (SART/AIS-SART) battery expiry date checked, test signal verified.", "rule": "SOLAS Ch IV", "default_status": "Y"}
    ],
    "DG (Dangerous Goods)": [
        {"id": "1.1", "item": "Mechanical ventilation in cargo spaces functional, safety guards in place.", "rule": "SOLAS Ch II-2 Reg 19", "default_status": "Y"},
        {"id": "1.2", "item": "Gas detection system in cargo pump rooms calibrated and alarms operational.", "rule": "SOLAS Ch II-2 Reg 4", "default_status": "Y"},
        {"id": "1.3", "item": "Electrical equipment in cargo spaces certified safe / explosion-proof type.", "rule": "SOLAS Ch II-2 Reg 19", "default_status": "Y"},
        {"id": "1.4", "item": "Water spraying arrangements and fire hose coverage for cargo spaces verified.", "rule": "SOLAS Ch II-2 Reg 19", "default_status": "Y"},
        {"id": "1.5", "item": "Personal protective clothing and breathing apparatus sets for dangerous cargo service check.", "rule": "SOLAS Ch II-2 Reg 19", "default_status": "Y"}
    ],
    "IMSBC (Solid Bulk Cargoes)": [
        {"id": "1.1", "item": "Carriage requirements for Group A, B, or C cargoes verified matching IMSBC booklet.", "rule": "SOLAS Ch VI", "default_status": "Y"},
        {"id": "1.2", "item": "Cargo space bilge high-level alarms and drainage arrangements tested.", "rule": "SOLAS Ch VI", "default_status": "Y"},
        {"id": "1.3", "item": "Gas monitoring instruments (Oxygen, Methane, CO) calibrated and functional.", "rule": "SOLAS Ch VI", "default_status": "Y"},
        {"id": "1.4", "item": "Cargo securing manual onboard and cargo trimming procedures documented.", "rule": "SOLAS Ch VI", "default_status": "Y"},
        {"id": "1.5", "item": "Electrical isolation of equipment in cargo spaces verified for bulk operations.", "rule": "SOLAS Ch VI", "default_status": "Y"}
    ],
    "IAFS (Anti-Fouling Systems)": [
        {"id": "1.1", "item": "IAFS Certificate onboard and organotin compound-free paint declaration verified.", "rule": "IAFSC Reg 1", "default_status": "Y"},
        {"id": "1.2", "item": "Hull anti-fouling coating visual condition checked and found free of damage.", "rule": "IAFSC Reg 1", "default_status": "Y"},
        {"id": "1.3", "item": "Paint technical specifications and manufacturer data sheets confirm no tin compounds.", "rule": "IAFSC Reg 1", "default_status": "Y"},
        {"id": "1.4", "item": "Sealer coat records checked for ships holding active older anti-fouling systems.", "rule": "IAFSC Reg 1", "default_status": "Y"},
        {"id": "1.5", "item": "Paint application logs and shipyard records confirm correct paint type used.", "rule": "IAFSC Reg 1", "default_status": "Y"}
    ],
    "ITC (International Tonnage)": [
        {"id": "1.1", "item": "Gross and Net Tonnage calculations match calculations listed in Tonnage Certificate.", "rule": "ITC 1969", "default_status": "Y"},
        {"id": "1.2", "item": "Underdeck and superstructure enclosed spaces measurements verified.", "rule": "ITC 1969", "default_status": "Y"},
        {"id": "1.3", "item": "Excluded spaces (e.g. open spaces) meet the specific exclusion criteria.", "rule": "ITC 1969", "default_status": "Y"},
        {"id": "1.4", "item": "Vessel particulars (Length, Breadth, Moulded Depth) match physical construction.", "rule": "ITC 1969", "default_status": "Y"},
        {"id": "1.5", "item": "Vessel modifications affecting tonnage records (if any) checked and recalculated.", "rule": "ITC 1969", "default_status": "Y"}
    ],
    "IHM (Inventory of Hazardous Materials)": [
        {"id": "1.1", "item": "Inventory of Hazardous Materials (IHM) Part I verified and updated onboard.", "rule": "EU SRR / HKC", "default_status": "Y"},
        {"id": "1.2", "item": "Statement of Compliance (SOC) on IHM valid and available for inspection.", "rule": "EU SRR / HKC", "default_status": "Y"},
        {"id": "1.3", "item": "Supplier Material Declarations (MD) and Supplier Declarations of Conformity (SDoC) complete.", "rule": "EU SRR / HKC", "default_status": "Y"},
        {"id": "1.4", "item": "Visual inspection shows no unauthorized asbestos or ozone-depleting substances in new installations.", "rule": "EU SRR / HKC", "default_status": "Y"},
        {"id": "1.5", "item": "IHM maintenance logbook maintained for additions and replacements of equipment.", "rule": "EU SRR / HKC", "default_status": "Y"}
    ],
    "MLC (Maritime Labour Convention)": [
        {"id": "1.1", "item": "Seafarers Employment Agreements (SEA) checked: signatures and conditions comply.", "rule": "MLC 2006", "default_status": "Y"},
        {"id": "1.2", "item": "Food and catering hygiene checks: galley, dry store, and cold room temperatures compliant.", "rule": "MLC 2006", "default_status": "Y"},
        {"id": "1.3", "item": "Accommodation heating, ventilation, and lighting levels check.", "rule": "MLC 2006", "default_status": "Y"},
        {"id": "1.4", "item": "Rest hours records checked: compliance with daily/weekly limits verified with signatures.", "rule": "MLC 2006", "default_status": "Y"},
        {"id": "1.5", "item": "Medical cabinet inventory check: medications inside expiry date, certificates valid.", "rule": "MLC 2006", "default_status": "Y"}
    ],
    "SMC (Safety Management Certificate)": [
        {"id": "1.1", "item": "Safety Management System (SMS) implementation verified: safety drills logs updated.", "rule": "ISM Code", "default_status": "Y"},
        {"id": "1.2", "item": "Internal audit reports onboard and corrective actions for non-conformities completed.", "rule": "ISM Code", "default_status": "Y"},
        {"id": "1.3", "item": "Emergency drill logs: fire, abandon ship, oil spill, and rescue drills completed monthly.", "rule": "ISM Code", "default_status": "Y"},
        {"id": "1.4", "item": "Safety committee meeting minutes checked and master's review documented.", "rule": "ISM Code", "default_status": "Y"},
        {"id": "1.5", "item": "Maintenance system records: critical equipment tested and logbook updated.", "rule": "ISM Code", "default_status": "Y"}
    ],
    "ISSC (International Ship Security)": [
        {"id": "1.1", "item": "Ship Security Plan (SSP) approved, confidential, and master's security authority clear.", "rule": "ISPS Code", "default_status": "Y"},
        {"id": "1.2", "item": "Access control points, ship boarding security, and locks checked.", "rule": "ISPS Code", "default_status": "Y"},
        {"id": "1.3", "item": "Security drills and exercises completed quarterly and recorded in log.", "rule": "ISPS Code", "default_status": "Y"},
        {"id": "1.4", "item": "Restricted areas clearly marked, locked, and monitored.", "rule": "ISPS Code", "default_status": "Y"},
        {"id": "1.5", "item": "Ship Security Alert System (SSAS) and security level communication functional.", "rule": "ISPS Code", "default_status": "Y"}
    ],
    "SOPEP (Oil Pollution Emergency Plan)": [
        {"id": "1.1", "item": "Approved SOPEP manual onboard and oil spill response crew roles defined.", "rule": "MARPOL Annex I Reg 37", "default_status": "Y"},
        {"id": "1.2", "item": "Spill response equipment inventory check: absorbents, booms, sawdust, pumps complete.", "rule": "MARPOL Annex I Reg 37", "default_status": "Y"},
        {"id": "1.3", "item": "Emergency contact lists (coastal states and ports) updated and current.", "rule": "MARPOL Annex I Reg 37", "default_status": "Y"},
        {"id": "1.4", "item": "Oil spill emergency response drill logs updated and drills done quarterly.", "rule": "MARPOL Annex I Reg 37", "default_status": "Y"},
        {"id": "1.5", "item": "SOPEP locker marked, accessible, and inventory list signed.", "rule": "MARPOL Annex I Reg 37", "default_status": "Y"}
    ]
}

CHECKLIST_TEMPLATES = {}
TEMPLATE_METADATA_FIELDS = {}

for k, v in STATIC_TEMPLATES.items():
    CHECKLIST_TEMPLATES[k] = []
    TEMPLATE_METADATA_FIELDS[k] = []
    for x in v:
        CHECKLIST_TEMPLATES[k].append({
            "id": x.get("id"),
            "item": x.get("item"),
            "rule": x.get("rule", ""),
            "default_status": x.get("default_status", "Y")
        })

json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checklists_extracted.json")
if os.path.exists(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            extracted = json.load(f)
            mapping = {
                "IOPP": "ANNEX I IOPP (Oil Pollution Prevention)",
                "SPP": "ANNEX IV SPP (Sewage Pollution Prevention)",
                "IAPPC": "ANNEX VI IAPPC (Air Pollution Prevention)",
                "BWM": "BWM (Ballast Water Management)",
                "LL": "LL (International Load Line)",
                "SE": "SE (Safety Equipment)",
                "SC": "SC (Safety Construction)",
                "SR_0203": "SR (Safety Radio - Form 0203)",
                "SR_0300": "SR (Safety Radio - Form 0300)",
                "DG": "DG (Dangerous Goods)",
                "IMSBC": "IMSBC (Solid Bulk Cargoes)",
                "MLC": "MLC (Maritime Labour Convention)",
                "SMC": "SMC (Safety Management Certificate)",
                "ISSC": "ISSC (International Ship Security)"
            }
            for k, val in extracted.items():
                mapped_name = mapping.get(k, k)  # fallback to the key itself (e.g. ISM)
                
                # Support both the new dictionary format and legacy list format
                if isinstance(val, dict):
                    items_list = val.get("items", [])
                    metadata_fields = val.get("metadata_fields", [])
                else:
                    items_list = val
                    metadata_fields = []
                
                if mapped_name and items_list:
                    CHECKLIST_TEMPLATES[mapped_name] = []
                    TEMPLATE_METADATA_FIELDS[mapped_name] = metadata_fields
                    
                    for item in items_list:
                        item_no = item.get("item_no", "")
                        desc = item.get("description", "")
                        status = item.get("default_status", "Y")
                        
                        rule_match = re.search(r'\(([^)]*(?:MARPOL|SOLAS|BWM|ICLL|reg|regs|ISM|ISPS|MLC|ILO)[^)]*)\)', desc)
                        rule = rule_match.group(1) if rule_match else ""
                        if not rule:
                            if "IOPP" in mapped_name: rule = "MARPOL Annex I"
                            elif "SPP" in mapped_name: rule = "MARPOL Annex IV"
                            elif "IAPPC" in mapped_name: rule = "MARPOL Annex VI"
                            elif "BWM" in mapped_name: rule = "BWM D-2"
                            elif "LL" in mapped_name: rule = "ICLL 1966"
                            elif "SE" in mapped_name: rule = "SOLAS Ch II-2 & III"
                            elif "SC" in mapped_name: rule = "SOLAS Ch II-1"
                            elif "SR" in mapped_name: rule = "SOLAS Ch IV"
                            elif "DG" in mapped_name: rule = "SOLAS Ch II-2 Reg 19"
                            elif "IMSBC" in mapped_name: rule = "IMSBC Code"
                            elif "MLC" in mapped_name: rule = "MLC 2006"
                            elif "SMC" in mapped_name: rule = "ISM Code"
                            elif "ISSC" in mapped_name: rule = "ISPS Code"
                            elif "ISM" in mapped_name: rule = "ISM Code"
                            else: rule = "General Provision"
                            
                        CHECKLIST_TEMPLATES[mapped_name].append({
                            "id": item_no,
                            "item": desc,
                            "rule": rule,
                            "default_status": status
                        })
    except Exception as e:
        print("Error loading checklists_extracted.json:", e)

def get_clean_metadata_fields(template_name):
    fields = TEMPLATE_METADATA_FIELDS.get(template_name, [])
    clean_fields = []
    
    ignore_lower = {
        "ref no", "ref no.", "type (c/r)", "comments (c) / remarks (r)", "comments", "remarks", 
        "name and signature of phrs surveyor", "date / place of verification", "date / place of issuance", 
        "signature of phrs surveyor", "signature of master", "signature", "date", "place", "page", "phrs", 
        "surveyor", "master", "vessel", "ship", "imo", "gross tonnage", "deadweight", "port of registry", 
        "call sign", "class", "flag", "results", "item", "description", "rule", "status", "recommendation",
        "item no.", "item no", "description of item", "guidelines", "satisfactory", "yes", "no", "n/a", "na",
        "date of survey", "place of survey", "survey date", "surveyor name", "project no.", "project no", "project number",
        "gemi adı", "gemi adi", "imo numarası", "bayrak devleti", "klas kuruluşu", "gemi türü", "brüt tonaj", "detveyt tonaj",
        "y", "n", "c", "r", "c/r", "name of ship", "imo number", "gross tonnage (grt)", "deadweight (dwt)", "call sign",
        "port of registry / flag", "port of registry", "vessel type", "class", "stamp", "maker", "type",
        "satisfactory (1)", "very good (1)", "poor (1), (2)", "mark with", "comments (c)", "remarks (r)", "type (c/r/nc)",
        "type of ship", "names / imo number of ship(s) to be managed", "names", "place/date"
    }
    
    for f in fields:
        f_strip = str(f).strip()
        f_lower = f_strip.lower()
        if not f_strip:
            continue
        if f_lower in ignore_lower:
            continue
        if len(f_strip) <= 2:
            continue
        if re.match(r'^[\d\.\s\-\/\,]+$', f_strip):
            continue
        if f_strip.startswith('.') or re.match(r'^\d+\.', f_strip):
            continue
        if "regulation" in f_lower:
            continue
        if "mark with" in f_lower or "*" in f_lower:
            continue
        if any(x in f_lower for x in ["poor", "very good", "satisfactory", "signature", "stamp", "sign"]):
            continue
            
        clean_fields.append(f_strip)
        
    return clean_fields

