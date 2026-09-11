
System.Void SkillsComponent::ApplyBondStatus(BaseUnitController,SkillState) RVA=0x7b5dc0
007b5dc0 mov      qword ptr [rsp + 8], rbx                      
007b5dc5 mov      qword ptr [rsp + 0x10], rsi                   
007b5dca mov      qword ptr [rsp + 0x18], rdi                   
007b5dcf push     r12                                           
007b5dd1 push     r14                                           
007b5dd3 push     r15                                           
007b5dd5 sub      rsp, 0x70                                     
007b5dd9 mov      r15, r8                                       
007b5ddc mov      rsi, rdx                                      
007b5ddf mov      r14, rcx                                      
007b5de2 cmp      byte ptr [rip + 0x59b5c67], 0                 
007b5de9 jne      0x7b5e3a                                      
007b5deb lea      rcx, [rip + 0x55dd8e6]                        
007b5df2 call     0x5809f0                                      
007b5df7 lea      rcx, [rip + 0x55dda0a]                        
007b5dfe call     0x5809f0                                      
007b5e03 lea      rcx, [rip + 0x55ddb3e]                        
007b5e0a call     0x5809f0                                      
007b5e0f lea      rcx, [rip + 0x55c6682]                        
007b5e16 call     0x5809f0                                      
007b5e1b lea      rcx, [rip + 0x55a621e]                        
007b5e22 call     0x5809f0                                      
007b5e27 lea      rcx, [rip + 0x56400ba]                        
007b5e2e call     0x5809f0                                      
007b5e33 mov      byte ptr [rip + 0x59b5c16], 1                 
007b5e3a xor      edx, edx                                      
007b5e3c mov      rcx, r14                                      
007b5e3f call     0xc1c2f0                                      
007b5e44 test     al, al                                        
007b5e46 je       0x7b5e8d                                      
007b5e48 xor      edx, edx                                      
007b5e4a mov      rcx, r14                                      
007b5e4d call     0xc22370                                      
007b5e52 test     al, al                                        
007b5e54 jne      0x7b5e8d                                      
007b5e56 xor      edx, edx                                      
007b5e58 mov      rcx, r14                                      
007b5e5b call     0xc22520                                      
007b5e60 xor      r8d, r8d                                      
007b5e63 mov      rdx, qword ptr [rip + 0x564007e]              
007b5e6a mov      rcx, rax                                      
007b5e6d call     0xc66630                                      
007b5e72 lea      r11, [rsp + 0x70]                             
007b5e77 mov      rbx, qword ptr [r11 + 0x20]                   
007b5e7b mov      rsi, qword ptr [r11 + 0x28]                   
007b5e7f mov      rdi, qword ptr [r11 + 0x30]                   
007b5e83 mov      rsp, r11                                      
007b5e86 pop      r15                                           
007b5e88 pop      r14                                           
007b5e8a pop      r12                                           
007b5e8c ret                                                    
007b5e8d mov      rcx, qword ptr [rip + 0x55a61ac]              
007b5e94 cmp      dword ptr [rcx + 0xe4], 0                     
007b5e9b jne      0x7b5ea2                                      
007b5e9d call     0x580d30                                      
007b5ea2 xor      edx, edx                                      
007b5ea4 mov      rcx, rsi                                      
007b5ea7 call     0x443daf0                                     
007b5eac test     al, al                                        
007b5eae je       0x7b5e72                                      
007b5eb0 test     r15, r15                                      
007b5eb3 je       0x7b5fc7                                      
007b5eb9 xor      edx, edx                                      
007b5ebb mov      rcx, r15                                      
007b5ebe call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
007b5ec3 test     rax, rax                                      
007b5ec6 je       0x7b5fc7                                      
007b5ecc mov      rdx, qword ptr [rax + 0x258]                  
007b5ed3 test     rdx, rdx                                      
007b5ed6 je       0x7b5fc7                                      
007b5edc mov      r8, qword ptr [rip + 0x55c65b5]               
007b5ee3 lea      rcx, [rsp + 0x38]                             
007b5ee8 call     0x18d51f0                                     
007b5eed movups   xmm0, xmmword ptr [rsp + 0x38]                
007b5ef2 movups   xmmword ptr [rsp + 0x50], xmm0                
007b5ef7 movsd    xmm1, qword ptr [rsp + 0x48]                  
007b5efd movsd    qword ptr [rsp + 0x60], xmm1                  
007b5f03 xor      r12d, r12d                                    
007b5f06 mov      qword ptr [rsp + 0x38], r12                   
007b5f0b lea      rbx, [rsp + 0x50]                             
007b5f10 mov      qword ptr [rsp + 0x40], rbx                   
007b5f15 nop      word ptr [rax + rax]                          
007b5f20 mov      rdx, qword ptr [rip + 0x55dd8e1]              
007b5f27 lea      rcx, [rsp + 0x50]                             
007b5f2c call     0x299b470                                     
007b5f31 test     al, al                                        
007b5f33 je       0x7b5f93                                      
007b5f35 mov      rdi, qword ptr [rsp + 0x60]                   
007b5f3a test     rsi, rsi                                      
007b5f3d je       0x7b5fdc                                      
007b5f43 mov      rcx, qword ptr [rsi + 0x140]                  
007b5f4a test     rdi, rdi                                      
007b5f4d je       0x7b5fd7                                      
007b5f53 test     rcx, rcx                                      
007b5f56 je       0x7b5fd2                                      
007b5f58 mov      qword ptr [rsp + 0x20], r12                   
007b5f5d xor      r9d, r9d                                      
007b5f60 lea      r8d, [r9 - 1]                                 
007b5f64 mov      rdx, qword ptr [rdi + 0x10]                   
007b5f68 call     0x7eb870                                      System.Void StatusComponent::RemoveEffect(System.String,System.Int32,System.Boolean)
007b5f6d mov      rcx, qword ptr [rsi + 0x140]                  
007b5f74 test     rcx, rcx                                      
007b5f77 je       0x7b5fcd                                      
007b5f79 mov      qword ptr [rsp + 0x20], r12                   
007b5f7e mov      r9, qword ptr [r14 + 0x128]                   
007b5f85 mov      r8d, dword ptr [r15 + 0x3c]                   
007b5f89 mov      rdx, rdi                                      
007b5f8c call     0x7e4b40                                      System.Void StatusComponent::ApplyEffect(SkillStatus,System.Int32,BaseUnitController)
007b5f91 jmp      0x7b5f20                                      
007b5f93 mov      rdx, qword ptr [rip + 0x55dd73e]              
007b5f9a mov      rcx, rbx                                      
007b5f9d call     0x648670                                      System.Void Character::FootL()
007b5fa2 jmp      0x7b5e72                                      
007b5fa7 mov      rdx, qword ptr [rip + 0x55dd72a]              
007b5fae mov      rcx, qword ptr [rsp + 0x40]                   
007b5fb3 call     0x648670                                      System.Void Character::FootL()
007b5fb8 mov      rcx, qword ptr [rsp + 0x38]                   
007b5fbd test     rcx, rcx                                      
007b5fc0 jne      0x7b5fe2                                      
007b5fc2 jmp      0x7b5e72                                      
007b5fc7 call     0x580ca0                                      
007b5fcc nop                                                    
007b5fcd call     0x580ca0                                      
007b5fd2 call     0x580ca0                                      
007b5fd7 call     0x580ca0                                      
007b5fdc call     0x580ca0                                      
007b5fe1 nop                                                    
007b5fe2 call     0x57cc20                                      
007b5fe7 int3                                                   
007b5fe8 int3                                                   
007b5fe9 int3                                                   
007b5fea int3                                                   
007b5feb int3                                                   
007b5fec int3                                                   
007b5fed int3                                                   
007b5fee int3                                                   
007b5fef int3                                                   

System.Void SkillsComponent::Bond(BaseUnitController,SkillState) RVA=0x7b7c80
007b7c80 mov      qword ptr [rsp + 0x10], rbx                   
007b7c85 mov      qword ptr [rsp + 0x18], rbp                   
007b7c8a push     rsi                                           
007b7c8b sub      rsp, 0x20                                     
007b7c8f cmp      byte ptr [rip + 0x59b3db5], 0                 
007b7c96 mov      rsi, r8                                       
007b7c99 mov      rbp, rdx                                      
007b7c9c mov      rbx, rcx                                      
007b7c9f jne      0x7b7cd8                                      
007b7ca1 lea      rcx, [rip + 0x55f5a68]                        
007b7ca8 call     0x5809f0                                      
007b7cad lea      rcx, [rip + 0x55fb1ec]                        
007b7cb4 call     0x5809f0                                      
007b7cb9 lea      rcx, [rip + 0x55cfd58]                        
007b7cc0 call     0x5809f0                                      
007b7cc5 lea      rcx, [rip + 0x563e21c]                        
007b7ccc call     0x5809f0                                      
007b7cd1 mov      byte ptr [rip + 0x59b3d73], 1                 
007b7cd8 xor      edx, edx                                      
007b7cda mov      rcx, rbx                                      
007b7cdd call     0xc1c2f0                                      
007b7ce2 test     al, al                                        
007b7ce4 je       0x7b7d1f                                      
007b7ce6 xor      edx, edx                                      
007b7ce8 mov      rcx, rbx                                      
007b7ceb call     0xc22370                                      
007b7cf0 test     al, al                                        
007b7cf2 jne      0x7b7d1f                                      
007b7cf4 xor      edx, edx                                      
007b7cf6 mov      rcx, rbx                                      
007b7cf9 call     0xc22520                                      
007b7cfe mov      rdx, qword ptr [rip + 0x563e1e3]              
007b7d05 xor      r8d, r8d                                      
007b7d08 mov      rcx, rax                                      
007b7d0b mov      rbx, qword ptr [rsp + 0x38]                   
007b7d10 mov      rbp, qword ptr [rsp + 0x40]                   
007b7d15 add      rsp, 0x20                                     
007b7d19 pop      rsi                                           
007b7d1a jmp      0xc66630                                      
007b7d1f mov      rcx, qword ptr [rip + 0x55cfcf2]              
007b7d26 mov      qword ptr [rsp + 0x30], rdi                   
007b7d2b call     0x580c50                                      
007b7d30 xor      edx, edx                                      
007b7d32 mov      rcx, rax                                      
007b7d35 mov      rdi, rax                                      
007b7d38 call     0x645b10                                      System.Void GuildManager/__c__DisplayClass12_0::.ctor()
007b7d3d test     rdi, rdi                                      
007b7d40 je       0x7b7db8                                      
007b7d42 lea      rcx, [rdi + 0x10]                             
007b7d46 mov      qword ptr [rdi + 0x10], rbp                   
007b7d4a mov      rdx, rbp                                      
007b7d4d call     0x57fd40                                      
007b7d52 lea      rcx, [rdi + 0x18]                             
007b7d56 mov      qword ptr [rdi + 0x18], rbx                   
007b7d5a mov      rdx, rbx                                      
007b7d5d call     0x57fd40                                      
007b7d62 lea      rcx, [rdi + 0x20]                             
007b7d66 mov      qword ptr [rdi + 0x20], rsi                   
007b7d6a mov      rdx, rsi                                      
007b7d6d call     0x57fd40                                      
007b7d72 mov      rcx, qword ptr [rip + 0x55f5997]              
007b7d79 call     0x580c50                                      
007b7d7e mov      r8, qword ptr [rip + 0x55fb11b]               
007b7d85 xor      r9d, r9d                                      
007b7d88 mov      rdx, rdi                                      
007b7d8b mov      rcx, rax                                      
007b7d8e mov      rbx, rax                                      
007b7d91 call     0x69b670                                      
007b7d96 xor      r8d, r8d                                      
007b7d99 xorps    xmm1, xmm1                                    
007b7d9c mov      rcx, rbx                                      
007b7d9f mov      rdi, qword ptr [rsp + 0x30]                   
007b7da4 mov      rbx, qword ptr [rsp + 0x38]                   
007b7da9 mov      rbp, qword ptr [rsp + 0x40]                   
007b7dae add      rsp, 0x20                                     
007b7db2 pop      rsi                                           
007b7db3 jmp      0x823320                                      Schedule Scheduler::Invoke(Il2CppSystem.Action,System.Single)
007b7db8 call     0x580ca0                                      
007b7dbd int3                                                   
007b7dbe int3                                                   
007b7dbf int3                                                   

System.Void SkillsComponent::DoBondBegin(BaseUnitController,SkillState,System.Boolean) RVA=0x7ba940
007ba940 mov      qword ptr [rsp + 0x18], rsi                   
007ba945 push     rdi                                           
007ba946 push     r14                                           
007ba948 push     r15                                           
007ba94a sub      rsp, 0x30                                     
007ba94e cmp      byte ptr [rip + 0x59b10fa], 0                 
007ba955 movzx    r15d, r9b                                     
007ba959 mov      r14, r8                                       
007ba95c mov      rsi, rdx                                      
007ba95f mov      rdi, rcx                                      
007ba962 jne      0x7ba98f                                      
007ba964 lea      rcx, [rip + 0x563068d]                        
007ba96b call     0x5809f0                                      
007ba970 lea      rcx, [rip + 0x55cde01]                        
007ba977 call     0x5809f0                                      
007ba97c lea      rcx, [rip + 0x563b565]                        
007ba983 call     0x5809f0                                      
007ba988 mov      byte ptr [rip + 0x59b10c0], 1                 
007ba98f xor      edx, edx                                      
007ba991 mov      rcx, rdi                                      
007ba994 call     0xc1c2f0                                      
007ba999 test     al, al                                        
007ba99b je       0x7ba9d5                                      
007ba99d xor      edx, edx                                      
007ba99f mov      rcx, rdi                                      
007ba9a2 call     0xc22370                                      
007ba9a7 test     al, al                                        
007ba9a9 jne      0x7ba9d5                                      
007ba9ab xor      edx, edx                                      
007ba9ad mov      rcx, rdi                                      
007ba9b0 call     0xc22520                                      
007ba9b5 mov      rdx, qword ptr [rip + 0x563b52c]              
007ba9bc xor      r8d, r8d                                      
007ba9bf mov      rcx, rax                                      
007ba9c2 mov      rsi, qword ptr [rsp + 0x60]                   
007ba9c7 add      rsp, 0x30                                     
007ba9cb pop      r15                                           
007ba9cd pop      r14                                           
007ba9cf pop      rdi                                           
007ba9d0 jmp      0xc66630                                      
007ba9d5 mov      rcx, qword ptr [rip + 0x55cdd9c]              
007ba9dc mov      qword ptr [rsp + 0x50], rbx                   
007ba9e1 mov      qword ptr [rsp + 0x58], rbp                   
007ba9e6 mov      rbp, qword ptr [rdi + 0x1f0]                  
007ba9ed call     0x580c50                                      
007ba9f2 xor      edx, edx                                      
007ba9f4 mov      rcx, rax                                      
007ba9f7 mov      rbx, rax                                      
007ba9fa call     0x645b10                                      System.Void GuildManager/__c__DisplayClass12_0::.ctor()
007ba9ff test     rbx, rbx                                      
007baa02 je       0x7bab77                                      
007baa08 lea      rcx, [rbx + 0x10]                             
007baa0c mov      qword ptr [rbx + 0x10], rsi                   
007baa10 mov      rdx, rsi                                      
007baa13 call     0x57fd40                                      
007baa18 test     r14, r14                                      
007baa1b je       0x7bab77                                      
007baa21 mov      rdx, qword ptr [r14 + 0x10]                   
007baa25 lea      rcx, [rbx + 0x18]                             
007baa29 mov      qword ptr [rbx + 0x18], rdx                   
007baa2d call     0x57fd40                                      
007baa32 cmp      byte ptr [rip + 0x59b1020], 0                 
007baa39 jne      0x7baa4e                                      
007baa3b lea      rcx, [rip + 0x55b44e6]                        
007baa42 call     0x5809f0                                      
007baa47 mov      byte ptr [rip + 0x59b100b], 1                 
007baa4e xor      edx, edx                                      
007baa50 mov      rcx, r14                                      
007baa53 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
007baa58 test     rax, rax                                      
007baa5b je       0x7bab77                                      
007baa61 mov      rdx, qword ptr [rip + 0x55b44c0]              
007baa68 mov      rcx, qword ptr [rax + 0x258]                  
007baa6f call     0xf4ae00                                      
007baa74 test     rax, rax                                      
007baa77 je       0x7bab77                                      
007baa7d movd     xmm0, dword ptr [r14 + 0x3c]                  
007baa83 cvtdq2ps xmm0, xmm0                                    
007baa86 mulss    xmm0, dword ptr [rax + 0x1c]                  
007baa8b addss    xmm0, dword ptr [rax + 0x18]                  
007baa90 mov      byte ptr [rbx + 0x24], r15b                   
007baa94 movss    dword ptr [rbx + 0x20], xmm0                  
007baa99 test     rbp, rbp                                      
007baa9c je       0x7bab77                                      
007baaa2 mov      r8, qword ptr [rip + 0x563054f]               
007baaa9 inc      dword ptr [rbp + 0x1c]                        
007baaac mov      rcx, qword ptr [rbp + 0x10]                   
007baab0 movsxd   rdx, dword ptr [rbp + 0x18]                   
007baab4 test     rcx, rcx                                      
007baab7 je       0x7bab77                                      
007baabd cmp      edx, dword ptr [rcx + 0x18]                   
007baac0 jb       0x7baade                                      
007baac2 mov      rax, qword ptr [r8 + 0x20]                    
007baac6 mov      rdx, rbx                                      
007baac9 mov      rcx, rbp                                      
007baacc mov      r8, qword ptr [rax + 0xc0]                    
007baad3 mov      r8, qword ptr [r8 + 0x70]                     
007baad7 call     0x19b3d40                                     
007baadc jmp      0x7bab02                                      
007baade lea      eax, [rdx + 1]                                
007baae1 mov      dword ptr [rbp + 0x18], eax                   
007baae4 cmp      edx, dword ptr [rcx + 0x18]                   
007baae7 jae      0x7bab7d                                      
007baaed mov      qword ptr [rcx + rdx*8 + 0x20], rbx           
007baaf2 lea      rcx, [rcx + rdx*8]                            
007baaf6 add      rcx, 0x20                                     
007baafa mov      rdx, rbx                                      
007baafd call     0x57fd40                                      
007bab02 test     rsi, rsi                                      
007bab05 je       0x7bab77                                      
007bab07 mov      r8, qword ptr [r14 + 0x10]                    
007bab0b xor      ebx, ebx                                      
007bab0d mov      rdx, qword ptr [rsi + 0x30]                   
007bab11 mov      r9b, 1                                        
007bab14 mov      rcx, rdi                                      
007bab17 mov      qword ptr [rsp + 0x20], rbx                   
007bab1c call     0x7b54f0                                      System.Void SkillsComponent::AddBondEntry(FishNet.Object.NetworkObject,System.String,System.Boolean)
007bab21 mov      rdx, qword ptr [rdi + 0x128]                  
007bab28 test     rdx, rdx                                      
007bab2b je       0x7bab77                                      
007bab2d mov      rcx, qword ptr [rsi + 0x138]                  
007bab34 test     rcx, rcx                                      
007bab37 je       0x7bab77                                      
007bab39 mov      r8, qword ptr [r14 + 0x10]                    
007bab3d xor      r9d, r9d                                      
007bab40 mov      rdx, qword ptr [rdx + 0x30]                   
007bab44 mov      qword ptr [rsp + 0x20], rbx                   
007bab49 call     0x7b54f0                                      System.Void SkillsComponent::AddBondEntry(FishNet.Object.NetworkObject,System.String,System.Boolean)
007bab4e xor      r9d, r9d                                      
007bab51 mov      r8, r14                                       
007bab54 mov      rdx, rsi                                      
007bab57 mov      rcx, rdi                                      
007bab5a mov      rbx, qword ptr [rsp + 0x50]                   
007bab5f mov      rbp, qword ptr [rsp + 0x58]                   
007bab64 mov      rsi, qword ptr [rsp + 0x60]                   
007bab69 add      rsp, 0x30                                     
007bab6d pop      r15                                           
007bab6f pop      r14                                           
007bab71 pop      rdi                                           
007bab72 jmp      0x7b5dc0                                      System.Void SkillsComponent::ApplyBondStatus(BaseUnitController,SkillState)
007bab77 call     0x580ca0                                      
007bab7c int3                                                   
007bab7d call     0x580c90                                      
007bab82 int3                                                   
007bab83 int3                                                   
007bab84 int3                                                   
007bab85 int3                                                   
007bab86 int3                                                   
007bab87 int3                                                   
007bab88 int3                                                   
007bab89 int3                                                   
007bab8a int3                                                   
007bab8b int3                                                   
007bab8c int3                                                   
007bab8d int3                                                   
007bab8e int3                                                   
007bab8f int3                                                   
