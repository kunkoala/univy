"use client";

import { Session } from "next-auth";
import { getCsrfToken } from "next-auth/react";
import { useState } from "react";

const buttonStyles =
  "bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full";

type ButtonFastapiTestProps = {
  session: Session | null;
};

export default function ButtonFastapiTest({ session }: ButtonFastapiTestProps) {
  const [response, setResponse] = useState<string | undefined>();

  const buttonHandler = async () => {
    try {
      // Normally you'd use GET here, but we want to show how to do CSRF protection too,
      // Which with the default configuration doesn't happen on GET requests
      const csrfToken = await getCsrfToken();

      if (!csrfToken) {
        throw new Error("No csrf token");
      }

      const res = await fetch("fastapi/auth/test-auth", {
        method: "GET",
        credentials: "include",
        headers: {
          "X-XSRF-Token": csrfToken,
        },
      });
      const contentType = res.headers.get("content-type");
      let data;
      if (contentType && contentType.includes("application/json")) {
        data = await res.json();
      } else {
        data = await res.text();
      }

      setResponse(
        typeof data === "string" ? data : JSON.stringify(data, null, 2),
      );
    } catch (e) {
      console.error(e);
      setResponse("error");
    }
  };

  return (
    <main className="flex flex-col items-center justify-between p-24">
      <div className="flex flex-col items-center gap-2">
        Hello {session?.user?.name}
        <button className={buttonStyles} onClick={buttonHandler}>
          Talk to FastAPI!
        </button>
        {response ? <pre> {response} </pre> : <p>No response</p>}
      </div>
    </main>
  );
}
