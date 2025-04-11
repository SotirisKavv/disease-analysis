import streamlit as st
from openai import OpenAI
import json
import pandas as pd

# Setup OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_disease_info(disease_name):
    medication_format = """
    "name":"",
    "side_effects":[
        0: {"name": "", "description": "", "rating": ""},
        1: {"name": "", "description": "", "rating": ""},
        ...    
    ],
    "dosage":""
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
             {"role": "system", 
              "content": 
                f"""Please provide information on the following aspects for {disease_name}: 
                    1. Key Statistics, 
                    2. Recovery Options, 
                    3. Recommended Medications. 
                    Format the response in JSON with keys for 'name', 'statistics', 'total_cases' (this always has to be a number), 
                    'recovery_rate' (this always has to be a percentage), 'mortality_rate' (this always has to be a percentage),
                    'recovery_options' (explain each recovery option in detail), and 'medication' (make it a list and give some side 
                    effect examples and dosages for each). Regarding the side effects, provide a small description and a rating on the 
                    scale ("mild", "moderate", "severe"). Always use this json format for medication : {medication_format} .Return only 
                    raw valid JSON. Do not wrap it in backticks or markdown formatting. All numbers must be actual numeric values 
                    (e.g., 463000000, not "463 million")."""
            }
        ],
    )
    
    return response.choices[0].message.content

def display_disease_info(disease_info):
    try:
        # Parse the JSON response
        # print(repr(disease_info))
        info = json.loads(disease_info)
        
        recovery_rate = float(info['statistics']['recovery_rate'])
        mortality_rate = float(info['statistics']['mortality_rate'])
        
        chart_data = pd.DataFrame(
            {
                "Recovery Rate": [recovery_rate],
                "Mortality Rate": [mortality_rate],
            },
            index=["Rate"]
        )
        
        # Display key statistics
        st.write(f"### Statistics for {info['name']}")
        st.bar_chart(chart_data, stack=False)
        
        ro_tab, med_tab = st.tabs(["Recovery Options", "Medications"])
        with ro_tab:
            # Display Recovery Options
            st.write("## Recovery Options")
            recovery_options = info['recovery_options']
            for option, recovery in recovery_options.items():
                st.subheader(option.replace("_", " ").title())
                st.write(recovery)
            
        with med_tab:
            # Display Medications
            st.write("## Medications")
            medication_info = info['medication']
            for medication in medication_info:
                with st.expander(medication['name'], expanded=False):
                    with st.container():
                        st.write(f"### {medication['name']}")
                        st.write(f"💊 **Dosage:** {medication['dosage']}")
                        st.write("⚠️ **Side Effects:**")
                        for side_effect in medication['side_effects']:
                            st.write(f"- **{side_effect['name']} ({side_effect['rating']})**")
                            st.write(f"_{side_effect['description']}_")
        
        st.write(f"[Read more on WHO](https://www.who.int/news-room/fact-sheets/detail/{info['name'].replace(' ', '-').lower()})")
            
    except json.JSONDecodeError as e:
        st.error(f"Failed to decode the response into JSON. Please check the format of the OpenAI response. {e}")
            
        


# Title of the app
st.title("Disease Information Dashboard")

disease_name = st.text_input("Enter a disease name")

if disease_name:
    # Get disease information
    with st.spinner("Fetching disease information..."):
        disease_info = get_disease_info(disease_name)
        # st.write(disease_info)
        display_disease_info(disease_info)