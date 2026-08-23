from src.llm.client import get_llm_client, get_model


def test_groq_connection():
    client = get_llm_client()
    model = get_model()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: ParcelPilot OK",
            }
        ],
    )

    assert response.choices
    assert response.choices[0].message.content

    print(response.choices[0].message.content)