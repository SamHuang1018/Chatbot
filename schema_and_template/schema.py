tire_data_columns = ['品牌英文', '品牌中文', '數量', '輪胎規格', '金額', '類別', '品牌型號']

bolt_pattern_columns = ['尺寸', '品牌', '孔徑', '價格', '數量(組)', '型號', 'J數', 'ET值']

ragic_columns = {
    '新胎': '新胎',
    '國內二手': '二手胎',
    '外匯二手': '二手胎',
    '外匯過季胎': '二手胎',
    '國內新品庫存': '新胎',
    '過季新胎': '二手胎',
    '國內過季新胎': '二手胎',
    '外匯新古': '二手胎'
    }

ragic_user_columns = {
    '_subtable_1000626': '零件維修',
    '_subtable_1000611': '輪胎維修',
    '_subtable_1000642': '其他',
    '_subtable_1000612': '鋁圈維修',
    '稅金': '含稅價'
    }



tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_tire_data",
            "description": "有明確問到輪胎時才會呼叫，但是必須要有車輛的廠牌、型號",
            "parameters": {
                "type": "object",
                "properties": {
                    "make": {
                        "type": "string",
                        "description": "車廠",
                    },
                    "model": {
                        "type": "string",
                        "description": "車型",
                    }
                },
                "required": ["make", "model"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_tire_specification_data",
            "description": "如果要從輪胎的規格找資料就會從這裡拿，格式有可能會類似315/35/21或是315 35 21或是315/35R21",
            "parameters": {
                "type": "object",
                "properties": {
                    "specification": {
                        "type": "string",
                        "description": "規格",
                    }
                },
                "required": ["specification"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_tire_brand_data",
            "description": "如果只有輪胎品牌和型號時就會呼叫此函數，格式有可能會類似米其林 215/55/16 P4、Michelin 215/55/16 P4、米其林 P4 215/55/16、Michelin P4 215/55/16",
            "parameters": {
                "type": "object",
                "properties": {
                    "brand": {
                        "type": "string",
                        "description": "品牌",
                    },
                    "brand_model": {
                        "type": "string",
                        "description": "型號",
                    }
                },
                "required": ["make", "brand_model"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_tire_single_brand_data",
            "description": "如果只有輪胎品牌呼叫此函數，種類有MICHELIN、TOYO TIRES、VIKING、GITI、CONTINENTAL、GOODYEAR、BRIDGESTONE、PIRELLI、NANKANG、RYDANZ、MAXXIS、NEXEN、YOKOHAMA、HANKOOK、SAILUN、KUMHO、FALKEN、DUNLOP、General、SONAR、Luccini、NITTO、atr、Acceiera、Pinso tyres、Winrun、FEDERAL、STAR、ALTAS、ARIVO、FIREMAX、IMP、fireston、DAVANTI、SEIBERLING、ZESTION、LANDSAIL、DAYTON、LANDSPIDER、DEESTONE、KENDA TIRE、LINGLONG、MOMO、DURATURN、VREDESTEIN、ACHILLES RADIAL、PETLAS、trocmoh、COOPER、crossleader、gremax、HIFLY、CST、FARROAD、NEUTON、BFGOODRICH、BLACK HAWK、TRISTAR、TRIANGLE、westlake",
            "parameters": {
                "type": "object",
                "properties": {
                    "single_brand": {
                        "type": "string",
                        "description": "品牌",
                    }
                },
                "required": ["single_brand"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_tire_single_brand_model_data",
            "description": "如果只有輪胎型號呼叫此函數，型號舉例有PSEV、CF2、pcy4、PROTECH、PS5、CHAMPIRO ECO、CC6、GRIP、SAVER 4、HL33、PC6、PZ4、T005A、AS 3、R23、PS4 SUV、T001、MS800、GTX。",
            "parameters": {
                "type": "object",
                "properties": {
                    "single_brand_model": {
                        "type": "string",
                        "description": "型號",
                    }
                },
                "required": ["single_brand_model"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_bolt_pattern_specification_data",
            "description": "如果有鋁圈、輪圈、輪框規格就會呼叫此函數，格式有可能會類似5-112、5孔112、5 112、5/112",
            "parameters": {
                "type": "object",
                "properties": {
                    "specification": {
                        "type": "string",
                        "description": "規格",
                    }
                },
                "required": ["specification"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_bolt_pattern_data",
            "description": "有明確問到鋁圈、輪圈、輪框時才會呼叫，但是必須要有車輛的廠牌、型號、年份或是鋁圈規格",
            "parameters": {
                "type": "object",
                "properties": {
                    "make": {
                        "type": "string",
                        "description": "車廠",
                    },
                    "model": {
                        "type": "string",
                        "description": "車型",
                    },
                    "year": {
                        "type": "integer",
                        "description": "年份",
                    }
                },
                "required": ["make", "model", "year"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_license_plate_number_data",
            "description": "輸入車牌號碼就可以查到客戶資料",
            "parameters": {
                "type": "object",
                "properties": {
                    "license_plate_number": {
                        "type": "string",
                        "description": "車牌號碼",
                    }
                },
                "required": ["license_plate_number"],
            },
        }
    }
]
