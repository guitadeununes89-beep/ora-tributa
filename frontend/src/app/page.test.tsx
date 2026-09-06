import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Home from "./page";

describe("Home", () => {
  it("comunica o catálogo nacional e a única regra publicada sem exagerar cobertura", () => {
    render(<Home />);
    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("164 cClassTrib");
    expect(status).toHaveTextContent("163 de 164");
    expect(status).toHaveTextContent("1 regra publicada");
    expect(status).toHaveTextContent("ruleset piloto");
    expect(status).toHaveTextContent("0,61%");
    expect(status).toHaveTextContent("não é default de produção");
    expect(screen.getByRole("link", { name: /Cobertura normativa/ })).toHaveAttribute(
      "href", "/reforma-tributaria/cobertura",
    );
  });
});
