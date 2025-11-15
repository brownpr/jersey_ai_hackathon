import streamlit as st


def render():
    st.title("🤖 Prediction demo")

    st.write(
        "This is a **fake prediction model** just to demonstrate the UI. "
        "We combine a few sliders into a simple linear formula."
    )

    col1, col2 = st.columns(2)

    with col1:
        feature_1 = st.slider("Feature 1 (e.g. temperature)", 0.0, 100.0, 50.0)
        feature_2 = st.slider("Feature 2 (e.g. pH)", 0.0, 14.0, 7.0)
        feature_3 = st.slider("Feature 3 (e.g. agitation speed)", 0, 1000, 500)

    with col2:
        st.write("Model parameters (for demo)")
        weight_1 = st.number_input("Weight for Feature 1", value=0.5)
        weight_2 = st.number_input("Weight for Feature 2", value=2.0)
        weight_3 = st.number_input("Weight for Feature 3", value=0.01)
        bias = st.number_input("Bias", value=10.0)

    if st.button("Run prediction"):
        prediction = (
            weight_1 * feature_1
            + weight_2 * feature_2
            + weight_3 * feature_3
            + bias
        )
        st.success(f"Predicted value: **{prediction:.2f}**")
    else:
        st.info("Adjust the sliders/weights and click **Run prediction**.")
