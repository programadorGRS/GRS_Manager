Create Database manager_db2Hml

-- manager_db2.ClientIP definition

CREATE TABLE `ClientIP` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip_addr` varchar(255) NOT NULL,
  `rate_limit` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip_addr` (`ip_addr`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.EmailConnect definition

CREATE TABLE `EmailConnect` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email_to` varchar(500) NOT NULL,
  `email_cc` varchar(500) DEFAULT NULL,
  `email_bcc` varchar(500) DEFAULT NULL,
  `email_subject` varchar(500) DEFAULT NULL,
  `attachments` varchar(500) DEFAULT NULL,
  `status` tinyint(1) NOT NULL DEFAULT '1',
  `df_len` int DEFAULT NULL,
  `ped_proc` int DEFAULT NULL,
  `error` varchar(255) DEFAULT NULL,
  `obs` varchar(255) DEFAULT NULL,
  `email_date` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11044 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.EmpresaPrincipal definition

CREATE TABLE `EmpresaPrincipal` (
  `cod` int NOT NULL,
  `nome` varchar(255) NOT NULL,
  `ativo` tinyint(1) NOT NULL,
  `socnet` tinyint(1) NOT NULL,
  `configs_exporta_dados` varchar(255) DEFAULT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  `chaves_exporta_dados` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`cod`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.ExportaDadosWS definition

CREATE TABLE `ExportaDadosWS` (
  `id` int NOT NULL AUTO_INCREMENT,
  `request_method` varchar(20) NOT NULL,
  `request_url` varchar(255) NOT NULL,
  `request_body` varchar(2000) DEFAULT NULL,
  `response_status` int DEFAULT NULL,
  `response_text` varchar(2000) DEFAULT NULL,
  `parametros` varchar(2000) NOT NULL,
  `erro_soc` tinyint(1) NOT NULL,
  `msg_erro` varchar(255) DEFAULT NULL,
  `request_date` datetime NOT NULL,
  `id_empresa` int DEFAULT NULL,
  `obs` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=380940 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Grupo definition

CREATE TABLE `Grupo` (
  `id_grupo` int NOT NULL AUTO_INCREMENT,
  `nome_grupo` varchar(255) NOT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_grupo`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.LogAcoes definition

CREATE TABLE `LogAcoes` (
  `id_log` int NOT NULL AUTO_INCREMENT,
  `id_usuario` int NOT NULL,
  `username` varchar(255) NOT NULL,
  `tabela` varchar(50) NOT NULL,
  `acao` varchar(255) NOT NULL,
  `id_registro` int DEFAULT NULL,
  `nome_registro` varchar(255) DEFAULT NULL,
  `obs` varchar(1000) DEFAULT NULL,
  `data` date NOT NULL,
  `hora` time NOT NULL,
  PRIMARY KEY (`id_log`)
) ENGINE=InnoDB AUTO_INCREMENT=655807 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Login definition

CREATE TABLE `Login` (
  `id_log` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `tela` varchar(50) NOT NULL,
  `date_time` datetime NOT NULL,
  `ip` varchar(50) NOT NULL,
  `obs` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id_log`)
) ENGINE=InnoDB AUTO_INCREMENT=9485 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.RTC definition

CREATE TABLE `RTC` (
  `id_rtc` int NOT NULL,
  `nome_rtc` varchar(255) NOT NULL,
  PRIMARY KEY (`id_rtc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Status definition

CREATE TABLE `Status` (
  `id_status` int NOT NULL AUTO_INCREMENT,
  `nome_status` varchar(100) NOT NULL,
  `finaliza_processo` tinyint(1) NOT NULL,
  `status_padrao` tinyint(1) DEFAULT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_status`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.StatusLiberacao definition

CREATE TABLE `StatusLiberacao` (
  `id_status_lib` int NOT NULL AUTO_INCREMENT,
  `nome_status_lib` varchar(50) NOT NULL,
  `cor_tag` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_status_lib`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.StatusProcessamento definition

CREATE TABLE `StatusProcessamento` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.StatusRAC definition

CREATE TABLE `StatusRAC` (
  `id_status` int NOT NULL AUTO_INCREMENT,
  `nome_status` varchar(100) NOT NULL,
  `status_padrao` tinyint(1) DEFAULT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_status`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.TipoExame definition

CREATE TABLE `TipoExame` (
  `cod_tipo_exame` int NOT NULL,
  `nome_tipo_exame` varchar(100) NOT NULL,
  PRIMARY KEY (`cod_tipo_exame`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.TipoProcessamento definition

CREATE TABLE `TipoProcessamento` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.TipoUsuario definition

CREATE TABLE `TipoUsuario` (
  `id_role` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) NOT NULL,
  PRIMARY KEY (`id_role`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.alembic_version definition

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Empresa definition

CREATE TABLE `Empresa` (
  `id_empresa` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `cod_empresa` int NOT NULL,
  `nome_abrev` varchar(255) DEFAULT NULL,
  `razao_social_inicial` varchar(255) DEFAULT NULL,
  `razao_social` varchar(255) NOT NULL,
  `ativo` tinyint(1) NOT NULL,
  `emails` varchar(500) DEFAULT NULL,
  `cnpj` varchar(100) DEFAULT NULL,
  `uf` varchar(5) DEFAULT NULL,
  `subgrupo` varchar(50) DEFAULT NULL,
  `conv_exames` tinyint(1) DEFAULT '1',
  `conv_exames_emails` varchar(500) DEFAULT NULL,
  `conv_exames_corpo_email` int DEFAULT '1',
  `conv_exames_convocar_clinico` tinyint(1) DEFAULT '0',
  `conv_exames_nunca_realizados` tinyint(1) DEFAULT '0',
  `conv_exames_per_nunca_realizados` tinyint(1) DEFAULT '0',
  `conv_exames_pendentes` tinyint(1) DEFAULT '0',
  `conv_exames_pendentes_pcmso` tinyint(1) DEFAULT '0',
  `conv_exames_selecao` int DEFAULT '1',
  `exames_realizados` tinyint(1) DEFAULT '1',
  `exames_realizados_emails` varchar(500) DEFAULT NULL,
  `absenteismo` tinyint(1) DEFAULT '1',
  `absenteismo_emails` varchar(500) DEFAULT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  `last_server_update` datetime DEFAULT NULL,
  `dominios_email` varchar(100) DEFAULT NULL,
  `central_avisos_token` varchar(255) DEFAULT NULL,
  `logo` varchar(100) DEFAULT 'grs.png',
  `modelo_rtc` varchar(100) DEFAULT 'rtc_default.html',
  PRIMARY KEY (`id_empresa`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  CONSTRAINT `Empresa_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`)
) ENGINE=InnoDB AUTO_INCREMENT=637 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.EmpresaSOCNET definition

CREATE TABLE `EmpresaSOCNET` (
  `id_empresa` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `cod_empresa_referencia` int NOT NULL,
  `cod_empresa` int NOT NULL,
  `nome_empresa` varchar(255) NOT NULL,
  `emails` varchar(500) DEFAULT NULL,
  `ativo` tinyint(1) NOT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_empresa`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  CONSTRAINT `EmpresaSOCNET_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Exame definition

CREATE TABLE `Exame` (
  `id_exame` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `cod_exame` varchar(255) NOT NULL,
  `nome_exame` varchar(255) NOT NULL,
  `prazo` int DEFAULT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_exame`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  CONSTRAINT `Exame_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`)
) ENGINE=InnoDB AUTO_INCREMENT=653 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.HistoricoMandatos definition

CREATE TABLE `HistoricoMandatos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cod_mandato` int NOT NULL,
  `ativo` tinyint(1) NOT NULL,
  `cod_empresa_principal` int NOT NULL,
  `id_empresa` int NOT NULL,
  `cod_unidade` varchar(100) DEFAULT NULL,
  `nome_setor` varchar(255) DEFAULT NULL,
  `cod_funcionario` int NOT NULL,
  `nome_funcionario` varchar(255) DEFAULT NULL,
  `funcionario_eleito` tinyint(1) DEFAULT NULL,
  `funcionario_renunciou` tinyint(1) DEFAULT NULL,
  `tipo_estabilidade` int DEFAULT NULL,
  `descr_estabilidade` varchar(100) DEFAULT NULL,
  `tipo_representacao` varchar(20) DEFAULT NULL,
  `funcao` varchar(100) DEFAULT NULL,
  `tipo_situacao` varchar(10) DEFAULT NULL,
  `data_inicio_mandato` date DEFAULT NULL,
  `data_fim_mandato` date DEFAULT NULL,
  `data_candidatura` date DEFAULT NULL,
  `data_inicio_eleitoral` date DEFAULT NULL,
  `data_eleicao` date DEFAULT NULL,
  `data_inicio_processo` date DEFAULT NULL,
  `data_inicio_inscricao` date DEFAULT NULL,
  `data_fim_inscricao` date DEFAULT NULL,
  `data_prorrogacao` date DEFAULT NULL,
  `data_estabilidade` date DEFAULT NULL,
  `data_inclusao` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `HistoricoMandatos_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `HistoricoMandatos_ibfk_2` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`)
) ENGINE=InnoDB AUTO_INCREMENT=26197 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Job definition

CREATE TABLE `Job` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tabela` varchar(100) NOT NULL,
  `cod_empresa_principal` int NOT NULL,
  `id_empresa` int DEFAULT NULL,
  `qtd_inseridos` int NOT NULL DEFAULT '0',
  `qtd_atualizados` int NOT NULL DEFAULT '0',
  `ok` tinyint(1) NOT NULL DEFAULT '1',
  `erro` varchar(255) DEFAULT NULL,
  `data` date NOT NULL,
  `hora` time NOT NULL,
  PRIMARY KEY (`id`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `Job_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `Job_ibfk_2` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`)
) ENGINE=InnoDB AUTO_INCREMENT=2630411 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.MandatoConfigEmpresa definition

CREATE TABLE `MandatoConfigEmpresa` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_empresa` int NOT NULL,
  `load_hist` tinyint(1) NOT NULL DEFAULT '0',
  `monit_erros` tinyint(1) NOT NULL DEFAULT '0',
  `monit_venc` tinyint(1) NOT NULL DEFAULT '0',
  `emails` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `MandatoConfigEmpresa_ibfk_1` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`)
) ENGINE=InnoDB AUTO_INCREMENT=625 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.PedProcConfig definition

CREATE TABLE `PedProcConfig` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_empresa` int NOT NULL,
  `ativo` tinyint(1) DEFAULT '1',
  `periodo_timedelta_dias` int DEFAULT '731',
  `selecao` int DEFAULT '1',
  `convocar_clinico` tinyint(1) DEFAULT '0',
  `nunca_realizados` tinyint(1) DEFAULT '0',
  `per_nunca_realizados` tinyint(1) DEFAULT '0',
  `pendentes` tinyint(1) DEFAULT '0',
  `pendentes_pcmso` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `PedProcConfig_ibfk_1` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`)
) ENGINE=InnoDB AUTO_INCREMENT=625 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.PedidoProcessamento definition

CREATE TABLE `PedidoProcessamento` (
  `id_proc` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `cod_solicitacao` int NOT NULL,
  `id_empresa` int NOT NULL,
  `cod_empresa` int NOT NULL,
  `data_criacao` date NOT NULL,
  `resultado_importado` tinyint(1) NOT NULL,
  `relatorio_enviado` tinyint(1) NOT NULL,
  `parametro` varchar(500) NOT NULL,
  `obs` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id_proc`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `PedidoProcessamento_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `PedidoProcessamento_ibfk_2` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`)
) ENGINE=InnoDB AUTO_INCREMENT=223548 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Prestador definition

CREATE TABLE `Prestador` (
  `id_prestador` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `cod_prestador` int DEFAULT NULL,
  `nome_prestador` varchar(255) NOT NULL,
  `emails` varchar(500) DEFAULT NULL,
  `ativo` tinyint(1) NOT NULL,
  `solicitar_asos` tinyint DEFAULT '1',
  `cnpj` varchar(100) DEFAULT NULL,
  `uf` varchar(4) DEFAULT NULL,
  `razao_social` varchar(255) DEFAULT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  `last_server_update` datetime DEFAULT NULL,
  PRIMARY KEY (`id_prestador`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  CONSTRAINT `Prestador_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`)
) ENGINE=InnoDB AUTO_INCREMENT=2104 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Processamento definition

CREATE TABLE `Processamento` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tipo` int NOT NULL,
  `status` int NOT NULL DEFAULT '1',
  `erro` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `status` (`status`),
  KEY `tipo` (`tipo`),
  CONSTRAINT `Processamento_ibfk_1` FOREIGN KEY (`status`) REFERENCES `StatusProcessamento` (`id`),
  CONSTRAINT `Processamento_ibfk_2` FOREIGN KEY (`tipo`) REFERENCES `TipoProcessamento` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=411 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.RTCCargos definition

CREATE TABLE `RTCCargos` (
  `cod_cargo` varchar(255) DEFAULT NULL,
  `id_rtc` int DEFAULT NULL,
  KEY `id_rtc` (`id_rtc`),
  CONSTRAINT `RTCCargos_ibfk_1` FOREIGN KEY (`id_rtc`) REFERENCES `RTC` (`id_rtc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.RTCExames definition

CREATE TABLE `RTCExames` (
  `id_rtc` int DEFAULT NULL,
  `cod_tipo_exame` int DEFAULT NULL,
  `cod_exame` varchar(255) DEFAULT NULL,
  KEY `id_rtc` (`id_rtc`),
  KEY `cod_tipo_exame` (`cod_tipo_exame`),
  CONSTRAINT `RTCExames_ibfk_1` FOREIGN KEY (`id_rtc`) REFERENCES `RTC` (`id_rtc`),
  CONSTRAINT `RTCExames_ibfk_2` FOREIGN KEY (`cod_tipo_exame`) REFERENCES `TipoExame` (`cod_tipo_exame`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Unidade definition

CREATE TABLE `Unidade` (
  `id_unidade` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `id_empresa` int NOT NULL,
  `cod_unidade` varchar(255) NOT NULL,
  `nome_unidade` varchar(255) NOT NULL,
  `emails` varchar(500) DEFAULT NULL,
  `ativo` tinyint(1) NOT NULL,
  `conv_exames` tinyint(1) DEFAULT '0',
  `conv_exames_emails` varchar(500) DEFAULT NULL,
  `conv_exames_corpo_email` int DEFAULT '1',
  `cod_rh` varchar(255) DEFAULT NULL,
  `uf` varchar(10) DEFAULT NULL,
  `exames_realizados` tinyint(1) DEFAULT '0',
  `exames_realizados_emails` varchar(500) DEFAULT NULL,
  `absenteismo` tinyint(1) DEFAULT '0',
  `absenteismo_emails` varchar(500) DEFAULT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  `last_server_update` datetime DEFAULT NULL,
  PRIMARY KEY (`id_unidade`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `Unidade_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `Unidade_ibfk_2` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`)
) ENGINE=InnoDB AUTO_INCREMENT=17756 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Usuario definition

CREATE TABLE `Usuario` (
  `id_usuario` int NOT NULL AUTO_INCREMENT,
  `id_cookie` varchar(255) NOT NULL,
  `username` varchar(50) NOT NULL,
  `nome_usuario` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `celular` varchar(20) DEFAULT NULL,
  `telefone` varchar(20) DEFAULT NULL,
  `senha` varchar(300) NOT NULL,
  `otp` varchar(300) DEFAULT NULL,
  `chave_api` varchar(300) DEFAULT NULL,
  `tipo_usuario` int NOT NULL,
  `ativo` tinyint(1) NOT NULL,
  `foto_perfil` varchar(255) DEFAULT NULL,
  `ultimo_login` datetime DEFAULT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `id_cookie` (`id_cookie`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `tipo_usuario` (`tipo_usuario`),
  CONSTRAINT `Usuario_ibfk_1` FOREIGN KEY (`tipo_usuario`) REFERENCES `TipoUsuario` (`id_role`)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.UsuarioSOC definition

CREATE TABLE `UsuarioSOC` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `cod` int NOT NULL,
  `nome` varchar(300) DEFAULT NULL,
  `email` varchar(400) DEFAULT NULL,
  `tipo` varchar(255) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  CONSTRAINT `UsuarioSOC_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`)
) ENGINE=InnoDB AUTO_INCREMENT=90348 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.grupo_empresa definition

CREATE TABLE `grupo_empresa` (
  `id_grupo` int DEFAULT NULL,
  `id_empresa` int DEFAULT NULL,
  KEY `id_grupo` (`id_grupo`),
  KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `grupo_empresa_ibfk_1` FOREIGN KEY (`id_grupo`) REFERENCES `Grupo` (`id_grupo`),
  CONSTRAINT `grupo_empresa_ibfk_2` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.grupo_empresa_socnet definition

CREATE TABLE `grupo_empresa_socnet` (
  `id_grupo` int DEFAULT NULL,
  `id_empresa` int DEFAULT NULL,
  KEY `id_grupo` (`id_grupo`),
  KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `grupo_empresa_socnet_ibfk_1` FOREIGN KEY (`id_grupo`) REFERENCES `Grupo` (`id_grupo`),
  CONSTRAINT `grupo_empresa_socnet_ibfk_2` FOREIGN KEY (`id_empresa`) REFERENCES `EmpresaSOCNET` (`id_empresa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.grupo_prestador definition

CREATE TABLE `grupo_prestador` (
  `id_grupo` int DEFAULT NULL,
  `id_prestador` int DEFAULT NULL,
  KEY `id_grupo` (`id_grupo`),
  KEY `id_prestador` (`id_prestador`),
  CONSTRAINT `grupo_prestador_ibfk_1` FOREIGN KEY (`id_grupo`) REFERENCES `Grupo` (`id_grupo`),
  CONSTRAINT `grupo_prestador_ibfk_2` FOREIGN KEY (`id_prestador`) REFERENCES `Prestador` (`id_prestador`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.grupo_usuario definition

CREATE TABLE `grupo_usuario` (
  `id_grupo` int DEFAULT NULL,
  `id_usuario` int DEFAULT NULL,
  KEY `id_grupo` (`id_grupo`),
  KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `grupo_usuario_ibfk_1` FOREIGN KEY (`id_grupo`) REFERENCES `Grupo` (`id_grupo`),
  CONSTRAINT `grupo_usuario_ibfk_2` FOREIGN KEY (`id_usuario`) REFERENCES `Usuario` (`id_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Cargo definition

CREATE TABLE `Cargo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `id_empresa` int NOT NULL,
  `cod_cargo` varchar(255) NOT NULL,
  `nome_cargo` varchar(300) DEFAULT NULL,
  `ativo` int NOT NULL,
  `cbo` varchar(255) DEFAULT NULL,
  `cod_rh` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `id_empresa` (`id_empresa`),
  CONSTRAINT `Cargo_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `Cargo_ibfk_2` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`)
) ENGINE=InnoDB AUTO_INCREMENT=36871 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.ExamesRealizados definition

CREATE TABLE `ExamesRealizados` (
  `id_realizado` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `seq_ficha` int NOT NULL,
  `cod_funcionario` int NOT NULL,
  `cpf` varchar(30) DEFAULT NULL,
  `nome_funcionario` varchar(150) DEFAULT NULL,
  `data_criacao` date NOT NULL,
  `data_ficha` date NOT NULL,
  `data_resultado` date NOT NULL,
  `cod_tipo_exame` int NOT NULL,
  `id_prestador` int DEFAULT NULL,
  `id_empresa` int NOT NULL,
  `id_unidade` int NOT NULL,
  `id_exame` int NOT NULL,
  `cod_setor` varchar(255) DEFAULT NULL,
  `nome_setor` varchar(255) DEFAULT NULL,
  `cod_cargo` varchar(255) DEFAULT NULL,
  `nome_cargo` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_realizado`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `cod_tipo_exame` (`cod_tipo_exame`),
  KEY `id_prestador` (`id_prestador`),
  KEY `id_empresa` (`id_empresa`),
  KEY `id_unidade` (`id_unidade`),
  KEY `id_exame` (`id_exame`),
  CONSTRAINT `ExamesRealizados_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `ExamesRealizados_ibfk_2` FOREIGN KEY (`cod_tipo_exame`) REFERENCES `TipoExame` (`cod_tipo_exame`),
  CONSTRAINT `ExamesRealizados_ibfk_3` FOREIGN KEY (`id_prestador`) REFERENCES `Prestador` (`id_prestador`),
  CONSTRAINT `ExamesRealizados_ibfk_4` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`),
  CONSTRAINT `ExamesRealizados_ibfk_5` FOREIGN KEY (`id_unidade`) REFERENCES `Unidade` (`id_unidade`),
  CONSTRAINT `ExamesRealizados_ibfk_6` FOREIGN KEY (`id_exame`) REFERENCES `Exame` (`id_exame`)
) ENGINE=InnoDB AUTO_INCREMENT=1037150 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Funcionario definition

CREATE TABLE `Funcionario` (
  `id_funcionario` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `cod_funcionario` int NOT NULL,
  `nome_funcionario` varchar(100) DEFAULT NULL,
  `cpf_funcionario` varchar(20) DEFAULT NULL,
  `id_empresa` int NOT NULL,
  `id_unidade` int DEFAULT NULL,
  `cod_setor` varchar(100) DEFAULT NULL,
  `nome_setor` varchar(100) DEFAULT NULL,
  `cod_cargo` varchar(100) DEFAULT NULL,
  `nome_cargo` varchar(100) DEFAULT NULL,
  `situacao` varchar(50) DEFAULT NULL,
  `data_adm` date DEFAULT NULL,
  `data_dem` date DEFAULT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  PRIMARY KEY (`id_funcionario`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `id_empresa` (`id_empresa`),
  KEY `id_unidade` (`id_unidade`),
  CONSTRAINT `Funcionario_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `Funcionario_ibfk_2` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`),
  CONSTRAINT `Funcionario_ibfk_3` FOREIGN KEY (`id_unidade`) REFERENCES `Unidade` (`id_unidade`)
) ENGINE=InnoDB AUTO_INCREMENT=518326 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.MandatoConfigUnidade definition

CREATE TABLE `MandatoConfigUnidade` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_unidade` int NOT NULL,
  `monit_erros` tinyint(1) NOT NULL DEFAULT '0',
  `monit_venc` tinyint(1) NOT NULL DEFAULT '0',
  `emails` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_unidade` (`id_unidade`),
  CONSTRAINT `MandatoConfigUnidade_ibfk_1` FOREIGN KEY (`id_unidade`) REFERENCES `Unidade` (`id_unidade`)
) ENGINE=InnoDB AUTO_INCREMENT=17172 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Pedido definition

CREATE TABLE `Pedido` (
  `id_ficha` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `seq_ficha` int NOT NULL,
  `cod_funcionario` int NOT NULL,
  `cpf` varchar(30) DEFAULT NULL,
  `nome_funcionario` varchar(150) DEFAULT NULL,
  `data_ficha` date NOT NULL,
  `cod_tipo_exame` int NOT NULL,
  `id_prestador` int DEFAULT NULL,
  `id_empresa` int NOT NULL,
  `id_unidade` int NOT NULL,
  `id_status` int NOT NULL,
  `id_status_rac` int NOT NULL DEFAULT '1',
  `prazo` int DEFAULT NULL,
  `prev_liberacao` date DEFAULT NULL,
  `id_status_lib` int NOT NULL,
  `data_recebido` date DEFAULT NULL,
  `data_comparecimento` date DEFAULT NULL,
  `obs` varchar(255) DEFAULT NULL,
  `data_inclusao` datetime NOT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  `last_server_update` datetime DEFAULT NULL,
  PRIMARY KEY (`id_ficha`),
  UNIQUE KEY `seq_ficha` (`seq_ficha`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `cod_tipo_exame` (`cod_tipo_exame`),
  KEY `id_prestador` (`id_prestador`),
  KEY `id_empresa` (`id_empresa`),
  KEY `id_unidade` (`id_unidade`),
  KEY `id_status` (`id_status`),
  KEY `id_status_lib` (`id_status_lib`),
  KEY `id_status_rac` (`id_status_rac`),
  CONSTRAINT `Pedido_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `Pedido_ibfk_2` FOREIGN KEY (`cod_tipo_exame`) REFERENCES `TipoExame` (`cod_tipo_exame`),
  CONSTRAINT `Pedido_ibfk_3` FOREIGN KEY (`id_prestador`) REFERENCES `Prestador` (`id_prestador`),
  CONSTRAINT `Pedido_ibfk_4` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`),
  CONSTRAINT `Pedido_ibfk_5` FOREIGN KEY (`id_unidade`) REFERENCES `Unidade` (`id_unidade`),
  CONSTRAINT `Pedido_ibfk_6` FOREIGN KEY (`id_status`) REFERENCES `Status` (`id_status`),
  CONSTRAINT `Pedido_ibfk_7` FOREIGN KEY (`id_status_lib`) REFERENCES `StatusLiberacao` (`id_status_lib`),
  CONSTRAINT `Pedido_ibfk_8` FOREIGN KEY (`id_status_rac`) REFERENCES `StatusRAC` (`id_status`)
) ENGINE=InnoDB AUTO_INCREMENT=235762 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.PedidoSOCNET definition

CREATE TABLE `PedidoSOCNET` (
  `id_ficha` int NOT NULL AUTO_INCREMENT,
  `seq_ficha` int NOT NULL,
  `cod_empresa_principal` int NOT NULL,
  `cod_empresa_referencia` int NOT NULL,
  `cod_funcionario` int NOT NULL,
  `cpf` varchar(30) DEFAULT NULL,
  `nome_funcionario` varchar(150) NOT NULL,
  `data_ficha` date NOT NULL,
  `cod_tipo_exame` int NOT NULL,
  `id_prestador` int DEFAULT NULL,
  `id_empresa` int NOT NULL,
  `id_status` int NOT NULL,
  `id_status_rac` int NOT NULL DEFAULT '1',
  `data_recebido` date DEFAULT NULL,
  `data_comparecimento` date DEFAULT NULL,
  `obs` varchar(255) DEFAULT NULL,
  `data_inclusao` datetime DEFAULT NULL,
  `data_alteracao` datetime DEFAULT NULL,
  `incluido_por` varchar(50) DEFAULT NULL,
  `alterado_por` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_ficha`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `cod_tipo_exame` (`cod_tipo_exame`),
  KEY `id_prestador` (`id_prestador`),
  KEY `id_empresa` (`id_empresa`),
  KEY `id_status` (`id_status`),
  KEY `id_status_rac` (`id_status_rac`),
  CONSTRAINT `PedidoSOCNET_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `PedidoSOCNET_ibfk_2` FOREIGN KEY (`cod_tipo_exame`) REFERENCES `TipoExame` (`cod_tipo_exame`),
  CONSTRAINT `PedidoSOCNET_ibfk_3` FOREIGN KEY (`id_prestador`) REFERENCES `Prestador` (`id_prestador`),
  CONSTRAINT `PedidoSOCNET_ibfk_4` FOREIGN KEY (`id_empresa`) REFERENCES `EmpresaSOCNET` (`id_empresa`),
  CONSTRAINT `PedidoSOCNET_ibfk_5` FOREIGN KEY (`id_status`) REFERENCES `Status` (`id_status`),
  CONSTRAINT `PedidoSOCNET_ibfk_7` FOREIGN KEY (`id_status_rac`) REFERENCES `StatusRAC` (`id_status`)
) ENGINE=InnoDB AUTO_INCREMENT=6864 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.Absenteismo definition

CREATE TABLE `Absenteismo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cod_empresa_principal` int NOT NULL,
  `id_funcionario` int NOT NULL,
  `id_empresa` int NOT NULL,
  `id_unidade` int NOT NULL,
  `tipo_licenca` varchar(255) DEFAULT NULL,
  `cod_medico` int DEFAULT NULL,
  `nome_medico` varchar(255) DEFAULT NULL,
  `data_ficha` date NOT NULL,
  `data_inicio_licenca` date DEFAULT NULL,
  `data_fim_licenca` date DEFAULT NULL,
  `afast_horas` tinyint(1) DEFAULT NULL,
  `hora_inicio_licenca` int DEFAULT NULL,
  `hora_fim_licenca` int DEFAULT NULL,
  `motivo_licenca` varchar(255) DEFAULT NULL,
  `cid_contestado` varchar(255) DEFAULT NULL,
  `cod_cid` varchar(255) DEFAULT NULL,
  `tipo_cid` varchar(255) DEFAULT NULL,
  `solicitante` varchar(255) DEFAULT NULL,
  `data_inclusao_licenca` date DEFAULT NULL,
  `dias_afastado` int DEFAULT NULL,
  `periodo_afastado` int DEFAULT NULL,
  `abonado` tinyint(1) DEFAULT NULL,
  `cid` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `id_funcionario` (`id_funcionario`),
  KEY `id_empresa` (`id_empresa`),
  KEY `id_unidade` (`id_unidade`),
  CONSTRAINT `Absenteismo_ibfk_1` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `Absenteismo_ibfk_2` FOREIGN KEY (`id_funcionario`) REFERENCES `Funcionario` (`id_funcionario`),
  CONSTRAINT `Absenteismo_ibfk_3` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`),
  CONSTRAINT `Absenteismo_ibfk_4` FOREIGN KEY (`id_unidade`) REFERENCES `Unidade` (`id_unidade`)
) ENGINE=InnoDB AUTO_INCREMENT=336551 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- manager_db2.ConvExames definition

CREATE TABLE `ConvExames` (
  `id_conv` int NOT NULL AUTO_INCREMENT,
  `id_proc` int NOT NULL,
  `cod_empresa_principal` int NOT NULL,
  `id_empresa` int NOT NULL,
  `id_unidade` int NOT NULL,
  `id_funcionario` int NOT NULL,
  `id_exame` int NOT NULL,
  `periodicidade` int DEFAULT NULL,
  `data_adm` date DEFAULT NULL,
  `ult_pedido` date DEFAULT NULL,
  `data_res` date DEFAULT NULL,
  `refazer` date DEFAULT NULL,
  PRIMARY KEY (`id_conv`),
  KEY `id_proc` (`id_proc`),
  KEY `cod_empresa_principal` (`cod_empresa_principal`),
  KEY `id_empresa` (`id_empresa`),
  KEY `id_unidade` (`id_unidade`),
  KEY `id_funcionario` (`id_funcionario`),
  KEY `id_exame` (`id_exame`),
  CONSTRAINT `ConvExames_ibfk_1` FOREIGN KEY (`id_proc`) REFERENCES `PedidoProcessamento` (`id_proc`),
  CONSTRAINT `ConvExames_ibfk_2` FOREIGN KEY (`cod_empresa_principal`) REFERENCES `EmpresaPrincipal` (`cod`),
  CONSTRAINT `ConvExames_ibfk_3` FOREIGN KEY (`id_empresa`) REFERENCES `Empresa` (`id_empresa`),
  CONSTRAINT `ConvExames_ibfk_4` FOREIGN KEY (`id_unidade`) REFERENCES `Unidade` (`id_unidade`),
  CONSTRAINT `ConvExames_ibfk_5` FOREIGN KEY (`id_funcionario`) REFERENCES `Funcionario` (`id_funcionario`),
  CONSTRAINT `ConvExames_ibfk_6` FOREIGN KEY (`id_exame`) REFERENCES `Exame` (`id_exame`)
) ENGINE=InnoDB AUTO_INCREMENT=119074957 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;