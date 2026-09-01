import { NextResponse } from "next/server";

export async function GET() {
    try {
        const backendUrl = "http://127.0.0.1:8000/health";
        const r = await fetch(backendUrl, { method: "GET" });
        const data = await r.json();
        return NextResponse.json(data, { status: r.status });
    } catch (e: any) {
        return NextResponse.json(
            {
                error: "Backend unavailable",
                message: String(e),
            },
            { status: 503 }
        );
    }
}