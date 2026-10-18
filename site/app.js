(() => {
  const repo = window.MINIX8_REPOSITORY || "";
  const version = window.MINIX8_VERSION || "1.1.0";
  document.querySelectorAll("[data-version]").forEach((node) => { node.textContent = `v${version}`; });
  const usableRepo = repo && !repo.includes("__REPOSITORY__") && repo.includes("/");
  const issueLink = document.querySelector("#issue-link");
  const newIssueLink = document.querySelector("#new-issue-link");
  const releaseLink = document.querySelector("#release-link");
  if (usableRepo) {
    issueLink.href = `https://github.com/${repo}/issues/new?template=bug.yml`;
    newIssueLink.href = `https://github.com/${repo}/issues/new/choose`;
    releaseLink.href = `https://github.com/${repo}/releases/latest`;
  } else {
    for (const link of [issueLink, newIssueLink]) {
      link.href = "#issues";
      link.title = "Configure o repositório no site/config.js para habilitar issues.";
    }
    releaseLink.href = "#downloads";
    releaseLink.title = "Configure o repositório no site/config.js para habilitar releases.";
  }

  const output = document.querySelector("#terminal-output");
  const form = document.querySelector("#terminal-form");
  const input = document.querySelector("#terminal-input");
  const replies = {
    help: "help · regs · step [n] · run [n] · reset · load · mem · set · quit",
    regs: "A=00 B=00 C=00 D=00  PC=0000 SP=FFFF  FLAGS=---  CICLOS=0",
    run: "ROM DEMO: Oi!\nA=21 B=00 C=00 D=00  PC=000A SP=FFFF  FLAGS=---  CICLOS=7 HALT",
    step: "1 INSTRUÇÃO EXECUTADA · PC=0001 · CONSULTE O EXECUTÁVEL PARA SIMULAR O CPU REAL",
    reset: "CPU E 64K RAM REINICIADAS · READY",
    mem: "0000: 01 4F 19 01 69 19 01 21 19 1A 00 00 00 00 00 00",
    about: "MINIX8 É UMA DEMONSTRAÇÃO DIDÁTICA EM C11 · RELEASES NA ABA DOWNLOADS",
    version: "VERSÃO ATUAL: CONSULTE A RELEASE OFICIAL NO GITHUB",
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const command = input.value.trim().slice(0, 120);
    if (!command) return;
    const line = document.createElement("p");
    line.className = "command";
    line.textContent = `minix8> ${command}`;
    output.append(line);
    const response = document.createElement("p");
    response.className = "response";
    response.textContent = replies[command.toLowerCase().split(/\s+/)[0]] || `COMANDO DEMONSTRATIVO NÃO IMPLEMENTADO: ${command}`;
    output.append(response);
    output.scrollTop = output.scrollHeight;
    input.value = "";
  });

  document.querySelector("#copy-rom").addEventListener("click", async () => {
    const bytes = "01 4F 19 01 69 19 01 21 19 1A";
    const status = document.querySelector("#copy-status");
    try {
      await navigator.clipboard.writeText(bytes);
      status.textContent = "COPIADO";
    } catch {
      status.textContent = bytes;
    }
  });
})();
