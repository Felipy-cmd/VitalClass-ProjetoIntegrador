CREATE DATABASE IF NOT EXISTS vital_class
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE vital_class;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    perfil ENUM('ADMIN', 'RECEPCAO', 'ENFERMEIRO', 'MEDICO') NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pacientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    data_nascimento DATE NOT NULL,
    sexo ENUM('MASCULINO', 'FEMININO', 'OUTRO') NOT NULL,
    telefone VARCHAR(20),
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE atendimentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    status ENUM('EM_ESPERA', 'EM_TRIAGEM', 'AGUARDANDO_ATENDIMENTO', 'ATENDIDO', 'CANCELADO') DEFAULT 'EM_ESPERA',
    motivo_consulta TEXT NOT NULL,
    chegada_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

CREATE TABLE triagens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    atendimento_id INT NOT NULL,
    enfermeiro_id INT NOT NULL,
    pressao_arterial VARCHAR(20),
    frequencia_cardiaca INT,
    temperatura DECIMAL(4,1),
    saturacao_oxigenio INT,
    frequencia_respiratoria INT,
    glicemia_capilar INT,
    sintoma_principal VARCHAR(150) NOT NULL,
    descricao_sintomas TEXT,
    alergias TEXT,
    escala_dor INT,
    especialidade VARCHAR(100),
    protocolo_assistencial VARCHAR(100),
    descricao_protocolo TEXT,
    classificacao ENUM('VERMELHO', 'LARANJA', 'AMARELO', 'VERDE', 'AZUL') NOT NULL,
    criada_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (atendimento_id) REFERENCES atendimentos(id),
    FOREIGN KEY (enfermeiro_id) REFERENCES usuarios(id)
);

INSERT INTO usuarios (nome, email, senha_hash, perfil)
VALUES (
    'Administrador',
    'admin@vitalclass.com',
    'scrypt:32768:8:1$Qx5f6KpOeWcdLkhh$33de8b8e4cbb61ab49a5a382d65f69735d5b36f82c731344e0865108a79d15534ae356f09f76c89991f78184f09509e9a43c8db7f809c366f055dc5d0cd0',
    'ADMIN'
);