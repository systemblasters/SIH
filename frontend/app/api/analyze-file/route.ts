import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = "http://127.0.0.1:8000/analyze-file";
const MAX_RETRIES = 5;
const RETRY_DELAY_MS = 800;

async function sleep(ms: number) {
    return new Promise((res) => setTimeout(res, ms));
}

export async function POST(req: NextRequest) {
    const formData = await req.formData();

    let lastError: any;

    for (let i = 0; i < MAX_RETRIES; i++) {
        try {
            const res = await fetch(BACKEND_URL, {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                const text = await res.text();
                throw new Error(`Backend error: ${res.status} ${text}`);
            }

            const data = await res.json();
            return NextResponse.json(data);
        } catch (e: any) {
            lastError = e;
            // Wait before retrying
            await sleep(RETRY_DELAY_MS);
        }
    }

    return NextResponse.json(
        {
            error: "Backend unavailable after retries",
            message: String(lastError),
        },
        { status: 503 }
    );
}