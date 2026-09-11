
System.Boolean SkillsComponent::CanHit(SkillState,BaseUnitController) RVA=0x7b89e0
007b89e0 push     rbx                                           
007b89e2 push     rbp                                           
007b89e3 push     r15                                           
007b89e5 sub      rsp, 0x30                                     
007b89e9 cmp      byte ptr [rip + 0x59b301c], 0                 
007b89f0 mov      rbx, r8                                       
007b89f3 mov      r15, rdx                                      
007b89f6 mov      rbp, rcx                                      
007b89f9 jne      0x7b8a26                                      
007b89fb lea      rcx, [rip + 0x55a363e]                        
007b8a02 call     0x5809f0                                      
007b8a07 lea      rcx, [rip + 0x55c127a]                        
007b8a0e call     0x5809f0                                      
007b8a13 lea      rcx, [rip + 0x55c113e]                        
007b8a1a call     0x5809f0                                      
007b8a1f mov      byte ptr [rip + 0x59b2fe6], 1                 
007b8a26 mov      rcx, qword ptr [rip + 0x55a3613]              
007b8a2d cmp      dword ptr [rcx + 0xe4], 0                     
007b8a34 jne      0x7b8a3b                                      
007b8a36 call     0x580d30                                      
007b8a3b mov      qword ptr [rsp + 0x50], rsi                   
007b8a40 xor      edx, edx                                      
007b8a42 mov      qword ptr [rsp + 0x58], rdi                   
007b8a47 mov      rcx, rbx                                      
007b8a4a mov      qword ptr [rsp + 0x68], r12                   
007b8a4f mov      qword ptr [rsp + 0x28], r13                   
007b8a54 mov      qword ptr [rsp + 0x20], r14                   
007b8a59 call     0x443daf0                                     
007b8a5e test     al, al                                        
007b8a60 je       0x7b8d8a                                      
007b8a66 test     rbx, rbx                                      
007b8a69 je       0x7b8dec                                      
007b8a6f mov      rax, qword ptr [rbx + 0x130]                  
007b8a76 test     rax, rax                                      
007b8a79 je       0x7b8dec                                      
007b8a7f cmp      dword ptr [rax + 0x140], 2                    
007b8a86 je       0x7b8d8a                                      
007b8a8c xor      edx, edx                                      
007b8a8e mov      rcx, rbx                                      
007b8a91 call     0xc22560                                      
007b8a96 mov      rcx, qword ptr [rbp + 0x128]                  
007b8a9d mov      r13d, eax                                     
007b8aa0 test     rcx, rcx                                      
007b8aa3 je       0x7b8dec                                      
007b8aa9 xor      edx, edx                                      
007b8aab call     0xc22560                                      
007b8ab0 mov      rcx, qword ptr [rbp + 0x128]                  
007b8ab7 cmp      r13d, eax                                     
007b8aba mov      dword ptr [rsp + 0x60], eax                   
007b8abe sete     r12b                                          
007b8ac2 test     rcx, rcx                                      
007b8ac5 je       0x7b8dec                                      
007b8acb mov      rcx, qword ptr [rcx + 0x130]                  
007b8ad2 test     rcx, rcx                                      
007b8ad5 je       0x7b8dec                                      
007b8adb xor      r8d, r8d                                      
007b8ade mov      rdx, rbx                                      
007b8ae1 call     0x84bcf0                                      System.Boolean CombatComponent::IsEnemy(BaseUnitController)
007b8ae6 mov      rcx, qword ptr [rbx + 0x148]                  
007b8aed movzx    esi, al                                       
007b8af0 test     rcx, rcx                                      
007b8af3 je       0x7b8dec                                      
007b8af9 xor      edx, edx                                      
007b8afb call     0x819f50                                      BaseUnitController SummoningComponent::get_Summoner()
007b8b00 mov      rcx, qword ptr [rip + 0x55a3539]              
007b8b07 mov      rdi, rax                                      
007b8b0a mov      r14, qword ptr [rbp + 0x128]                  
007b8b11 cmp      dword ptr [rcx + 0xe4], 0                     
007b8b18 jne      0x7b8b1f                                      
007b8b1a call     0x580d30                                      
007b8b1f xor      r8d, r8d                                      
007b8b22 mov      rdx, r14                                      
007b8b25 mov      rcx, rdi                                      
007b8b28 call     0x443d9f0                                     
007b8b2d test     al, al                                        
007b8b2f jne      0x7b8c4b                                      
007b8b35 mov      rax, qword ptr [rbp + 0x128]                  
007b8b3c test     rax, rax                                      
007b8b3f je       0x7b8dec                                      
007b8b45 mov      rcx, qword ptr [rax + 0x148]                  
007b8b4c test     rcx, rcx                                      
007b8b4f je       0x7b8dec                                      
007b8b55 xor      edx, edx                                      
007b8b57 call     0x819f50                                      BaseUnitController SummoningComponent::get_Summoner()
007b8b5c mov      rcx, qword ptr [rip + 0x55a34dd]              
007b8b63 mov      rdi, rax                                      
007b8b66 cmp      dword ptr [rcx + 0xe4], 0                     
007b8b6d jne      0x7b8b74                                      
007b8b6f call     0x580d30                                      
007b8b74 xor      r8d, r8d                                      
007b8b77 mov      rdx, rbx                                      
007b8b7a mov      rcx, rdi                                      
007b8b7d call     0x443d9f0                                     
007b8b82 test     al, al                                        
007b8b84 jne      0x7b8c4b                                      
007b8b8a mov      rax, qword ptr [rbp + 0x128]                  
007b8b91 test     rax, rax                                      
007b8b94 je       0x7b8dec                                      
007b8b9a mov      rcx, qword ptr [rax + 0x148]                  
007b8ba1 test     rcx, rcx                                      
007b8ba4 je       0x7b8dec                                      
007b8baa xor      edx, edx                                      
007b8bac call     0x819f50                                      BaseUnitController SummoningComponent::get_Summoner()
007b8bb1 mov      rcx, qword ptr [rip + 0x55a3488]              
007b8bb8 mov      rdi, rax                                      
007b8bbb cmp      dword ptr [rcx + 0xe4], 0                     
007b8bc2 jne      0x7b8bc9                                      
007b8bc4 call     0x580d30                                      
007b8bc9 xor      r8d, r8d                                      
007b8bcc xor      edx, edx                                      
007b8bce mov      rcx, rdi                                      
007b8bd1 call     0x443db80                                     
007b8bd6 test     al, al                                        
007b8bd8 jne      0x7b8bdf                                      
007b8bda xor      dil, dil                                      
007b8bdd jmp      0x7b8c4e                                      
007b8bdf mov      rax, qword ptr [rbp + 0x128]                  
007b8be6 test     rax, rax                                      
007b8be9 je       0x7b8dec                                      
007b8bef mov      rcx, qword ptr [rax + 0x148]                  
007b8bf6 test     rcx, rcx                                      
007b8bf9 je       0x7b8dec                                      
007b8bff xor      edx, edx                                      
007b8c01 call     0x819f50                                      BaseUnitController SummoningComponent::get_Summoner()
007b8c06 mov      rcx, qword ptr [rbx + 0x148]                  
007b8c0d mov      r14, rax                                      
007b8c10 test     rcx, rcx                                      
007b8c13 je       0x7b8dec                                      
007b8c19 xor      edx, edx                                      
007b8c1b call     0x819f50                                      BaseUnitController SummoningComponent::get_Summoner()
007b8c20 mov      rcx, qword ptr [rip + 0x55a3419]              
007b8c27 mov      rdi, rax                                      
007b8c2a cmp      dword ptr [rcx + 0xe4], 0                     
007b8c31 jne      0x7b8c38                                      
007b8c33 call     0x580d30                                      
007b8c38 xor      r8d, r8d                                      
007b8c3b mov      rdx, rdi                                      
007b8c3e mov      rcx, r14                                      
007b8c41 call     0x443d9f0                                     
007b8c46 movzx    edi, al                                       
007b8c49 jmp      0x7b8c4e                                      
007b8c4b mov      dil, 1                                        
007b8c4e test     r15, r15                                      
007b8c51 je       0x7b8dec                                      
007b8c57 mov      r14, qword ptr [r15 + 0x10]                   
007b8c5b xor      r8d, r8d                                      
007b8c5e mov      rdx, qword ptr [rip + 0x55c1023]              
007b8c65 mov      rcx, r14                                      
007b8c68 call     0x2df7870                                     
007b8c6d test     al, al                                        
007b8c6f jne      0x7b8c87                                      
007b8c71 mov      rdx, qword ptr [rip + 0x55c0ee0]              
007b8c78 xor      r8d, r8d                                      
007b8c7b mov      rcx, r14                                      
007b8c7e call     0x2df7870                                     
007b8c83 test     al, al                                        
007b8c85 je       0x7b8cdc                                      
007b8c87 mov      rax, qword ptr [rbp + 0x128]                  
007b8c8e test     rax, rax                                      
007b8c91 je       0x7b8dec                                      
007b8c97 mov      rcx, qword ptr [rax + 0x148]                  
007b8c9e test     rcx, rcx                                      
007b8ca1 je       0x7b8dec                                      
007b8ca7 xor      edx, edx                                      
007b8ca9 call     0x819db0                                      BaseUnitController SummoningComponent::get_Primary()
007b8cae mov      rcx, qword ptr [rip + 0x55a338b]              
007b8cb5 mov      rbp, rax                                      
007b8cb8 cmp      dword ptr [rcx + 0xe4], 0                     
007b8cbf jne      0x7b8cc6                                      
007b8cc1 call     0x580d30                                      
007b8cc6 xor      r8d, r8d                                      
007b8cc9 mov      rdx, rbx                                      
007b8ccc mov      rcx, rbp                                      
007b8ccf call     0x443d9f0                                     
007b8cd4 test     al, al                                        
007b8cd6 jne      0x7b8d8a                                      
007b8cdc xor      edx, edx                                      
007b8cde mov      rcx, r15                                      
007b8ce1 call     0x7d67d0                                      System.Boolean SkillState::get_IsHealing()
007b8ce6 test     al, al                                        
007b8ce8 je       0x7b8d0e                                      
007b8cea mov      rcx, qword ptr [rbx + 0x140]                  
007b8cf1 test     rcx, rcx                                      
007b8cf4 je       0x7b8dec                                      
007b8cfa xor      r8d, r8d                                      
007b8cfd lea      edx, [r8 + 2]                                 
007b8d01 call     0x7e9bc0                                      System.Boolean StatusComponent::Has(StatusComponent/StatusFlags)
007b8d06 test     al, al                                        
007b8d08 jne      0x7b8dcc                                      
007b8d0e xor      edx, edx                                      
007b8d10 mov      rcx, r15                                      
007b8d13 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
007b8d18 test     rax, rax                                      
007b8d1b je       0x7b8dec                                      
007b8d21 mov      rcx, qword ptr [rax + 0x208]                  
007b8d28 test     rcx, rcx                                      
007b8d2b je       0x7b8dec                                      
007b8d31 xor      edx, edx                                      
007b8d33 call     0x7d3700                                      System.Boolean ScaledValue::HasValue()
007b8d38 test     al, al                                        
007b8d3a jne      0x7b8dd0                                      
007b8d40 xor      edx, edx                                      
007b8d42 mov      rcx, r15                                      
007b8d45 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
007b8d4a test     rax, rax                                      
007b8d4d je       0x7b8dec                                      
007b8d53 movsxd   rax, dword ptr [rax + 0xe0]                   
007b8d5a cmp      eax, 6                                        
007b8d5d ja       0x7b8d8a                                      
007b8d5f mov      rcx, rax                                      
007b8d62 lea      rax, [rip - 0x7b8d69]                         
007b8d69 mov      edx, dword ptr [rax + rcx*4 + 0x7b8df4]       
007b8d70 add      rdx, rax                                      
007b8d73 jmp      rdx                                           
007b8d75 movzx    eax, sil                                      
007b8d79 jmp      0x7b8d8c                                      
007b8d7b xor      sil, 1                                        
007b8d7f movzx    eax, sil                                      
007b8d83 jmp      0x7b8d8c                                      
007b8d85 test     sil, sil                                      
007b8d88 je       0x7b8dc2                                      
007b8d8a xor      al, al                                        
007b8d8c mov      r14, qword ptr [rsp + 0x20]                   
007b8d91 mov      r13, qword ptr [rsp + 0x28]                   
007b8d96 mov      r12, qword ptr [rsp + 0x68]                   
007b8d9b mov      rdi, qword ptr [rsp + 0x58]                   
007b8da0 mov      rsi, qword ptr [rsp + 0x50]                   
007b8da5 add      rsp, 0x30                                     
007b8da9 pop      r15                                           
007b8dab pop      rbp                                           
007b8dac pop      rbx                                           
007b8dad ret                                                    
007b8dae movzx    eax, r12b                                     
007b8db2 jmp      0x7b8d8c                                      
007b8db4 or       dil, r12b                                     
007b8db7 movzx    eax, dil                                      
007b8dbb jmp      0x7b8d8c                                      
007b8dbd test     dil, dil                                      
007b8dc0 je       0x7b8d8a                                      
007b8dc2 cmp      r13d, dword ptr [rsp + 0x60]                  
007b8dc7 setne    al                                            
007b8dca jmp      0x7b8d8c                                      
007b8dcc mov      al, 1                                         
007b8dce jmp      0x7b8d8c                                      
007b8dd0 test     sil, sil                                      
007b8dd3 jne      0x7b8d8a                                      
007b8dd5 mov      rcx, qword ptr [rbx + 0x128]                  
007b8ddc test     rcx, rcx                                      
007b8ddf je       0x7b8dec                                      
007b8de1 xor      edx, edx                                      
007b8de3 call     0xaa7380                                      System.Boolean HealthComponent::get_IsAlive()
007b8de8 xor      al, 1                                         
007b8dea jmp      0x7b8d8c                                      
007b8dec call     0x580ca0                                      
007b8df1 int3                                                   
007b8df2 nop                                                    
007b8df4 jne      0x7b8d83                                      
007b8df6 jnp      0x7b8df8                                      
007b8df8 jnp      0x7b8d87                                      
007b8dfa jnp      0x7b8dfc                                      
007b8dfc test     dword ptr [rbp - 0x7251ff85], ecx             
007b8e02 jnp      0x7b8e04                                      
007b8e04 int3                                                   
007b8e05 lea      edi, [rbx]                                    
007b8e08 mov      ah, 0x8d                                      
007b8e0a jnp      0x7b8e0c                                      

System.Boolean PlayerController::CaptureInputs() RVA=0xabcec0
00abcec0 push     rbp                                           
00abcec2 push     r12                                           
00abcec4 push     r15                                           
00abcec6 lea      rbp, [rsp - 0x80]                             
00abcecb sub      rsp, 0x180                                    
00abced2 cmp      byte ptr [rip + 0x56affd9], 0                 
00abced9 mov      r15, rcx                                      
00abcedc jne      0xabcfb5                                      
00abcee2 lea      rcx, [rip + 0x52fa55f]                        
00abcee9 call     0x5809f0                                      
00abceee lea      rcx, [rip + 0x52bd4a3]                        
00abcef5 call     0x5809f0                                      
00abcefa lea      rcx, [rip + 0x52c7097]                        
00abcf01 call     0x5809f0                                      
00abcf06 lea      rcx, [rip + 0x52e03b3]                        
00abcf0d call     0x5809f0                                      
00abcf12 lea      rcx, [rip + 0x52fa0b7]                        
00abcf19 call     0x5809f0                                      
00abcf1e lea      rcx, [rip + 0x52f9f7b]                        
00abcf25 call     0x5809f0                                      
00abcf2a lea      rcx, [rip + 0x5287f0f]                        
00abcf31 call     0x5809f0                                      
00abcf36 lea      rcx, [rip + 0x529f103]                        
00abcf3d call     0x5809f0                                      
00abcf42 lea      rcx, [rip + 0x52d6e8f]                        
00abcf49 call     0x5809f0                                      
00abcf4e lea      rcx, [rip + 0x52af903]                        
00abcf55 call     0x5809f0                                      
00abcf5a lea      rcx, [rip + 0x52f1d37]                        
00abcf61 call     0x5809f0                                      
00abcf66 lea      rcx, [rip + 0x52b49a3]                        
00abcf6d call     0x5809f0                                      
00abcf72 lea      rcx, [rip + 0x52b2faf]                        
00abcf79 call     0x5809f0                                      
00abcf7e lea      rcx, [rip + 0x52fa70b]                        
00abcf85 call     0x5809f0                                      
00abcf8a lea      rcx, [rip + 0x527a20f]                        
00abcf91 call     0x5809f0                                      
00abcf96 lea      rcx, [rip + 0x533d46b]                        
00abcf9d call     0x5809f0                                      
00abcfa2 lea      rcx, [rip + 0x527722f]                        
00abcfa9 call     0x5809f0                                      
00abcfae mov      byte ptr [rip + 0x56afefd], 1                 
00abcfb5 xor      r12d, r12d                                    
00abcfb8 xorps    xmm0, xmm0                                    
00abcfbb xorps    xmm1, xmm1                                    
00abcfbe mov      qword ptr [rbp + 0xb0], r12                   
00abcfc5 xor      edx, edx                                      
00abcfc7 mov      qword ptr [rbp + 0xb8], r12                   
00abcfce mov      rcx, r15                                      
00abcfd1 mov      qword ptr [rsp + 0x70], r12                   
00abcfd6 movups   xmmword ptr [rsp + 0x78], xmm0                
00abcfdb movups   xmmword ptr [rbp - 0x78], xmm1                
00abcfdf call     0x441f380                                     
00abcfe4 test     al, al                                        
00abcfe6 je       0xabf586                                      
00abcfec mov      rax, qword ptr [rip + 0x52e02cd]              
00abcff3 mov      rcx, qword ptr [rax + 0xb8]                   
00abcffa cmp      byte ptr [rcx], r12b                          
00abcffd jne      0xabf586                                      
00abd003 movups   xmm0, xmmword ptr [r15 + 0x328]               
00abd00b lea      rcx, [r15 + 0x3e8]                            
00abd012 xor      edx, edx                                      
00abd014 movups   xmm1, xmmword ptr [r15 + 0x338]               
00abd01c movups   xmmword ptr [r15 + 0x398], xmm0               
00abd024 movups   xmm0, xmmword ptr [r15 + 0x348]               
00abd02c movups   xmmword ptr [r15 + 0x3a8], xmm1               
00abd034 movups   xmm1, xmmword ptr [r15 + 0x358]               
00abd03c movups   xmmword ptr [r15 + 0x3b8], xmm0               
00abd044 movups   xmm0, xmmword ptr [r15 + 0x368]               
00abd04c movups   xmmword ptr [r15 + 0x3c8], xmm1               
00abd054 movups   xmm1, xmmword ptr [r15 + 0x378]               
00abd05c movups   xmmword ptr [r15 + 0x3d8], xmm0               
00abd064 movups   xmm0, xmmword ptr [r15 + 0x388]               
00abd06c movups   xmmword ptr [r15 + 0x3e8], xmm1               
00abd074 movups   xmmword ptr [r15 + 0x3f8], xmm0               
00abd07c call     0x57fd40                                      
00abd081 xorps    xmm0, xmm0                                    
00abd084 movups   xmmword ptr [r15 + 0x328], xmm0               
00abd08c movups   xmmword ptr [r15 + 0x338], xmm0               
00abd094 movups   xmmword ptr [r15 + 0x348], xmm0               
00abd09c movups   xmmword ptr [r15 + 0x358], xmm0               
00abd0a4 movups   xmmword ptr [r15 + 0x368], xmm0               
00abd0ac movups   xmmword ptr [r15 + 0x378], xmm0               
00abd0b4 movups   xmmword ptr [r15 + 0x388], xmm0               
00abd0bc mov      rax, qword ptr [rip + 0x52fa385]              
00abd0c3 cmp      dword ptr [rax + 0xe4], r12d                  
00abd0ca jne      0xabd0db                                      
00abd0cc mov      rcx, rax                                      
00abd0cf call     0x580d30                                      
00abd0d4 mov      rax, qword ptr [rip + 0x52fa36d]              
00abd0db mov      rax, qword ptr [rax + 0xb8]                   
00abd0e2 mov      qword ptr [rsp + 0x1a0], rbx                  
00abd0ea mov      qword ptr [rsp + 0x178], rsi                  
00abd0f2 mov      qword ptr [rsp + 0x170], rdi                  
00abd0fa mov      rcx, qword ptr [rax + 0x70]                   
00abd0fe mov      qword ptr [rsp + 0x168], r13                  
00abd106 mov      qword ptr [rsp + 0x160], r14                  
00abd10e movaps   xmmword ptr [rsp + 0x150], xmm6               
00abd116 movaps   xmmword ptr [rsp + 0x140], xmm7               
00abd11e movaps   xmmword ptr [rsp + 0x130], xmm8               
00abd127 movaps   xmmword ptr [rsp + 0x120], xmm9               
00abd130 movaps   xmmword ptr [rsp + 0x110], xmm10              
00abd139 test     rcx, rcx                                      
00abd13c je       0xabf595                                      
00abd142 xor      edx, edx                                      
00abd144 call     0x9215d0                                      System.Boolean UIManager::get_IsShowingGameScreen()
00abd149 test     al, al                                        
00abd14b je       0xabf578                                      
00abd151 mov      rax, qword ptr [rip + 0x52fa2f0]              
00abd158 cmp      dword ptr [rax + 0xe4], r12d                  
00abd15f jne      0xabd170                                      
00abd161 mov      rcx, rax                                      
00abd164 call     0x580d30                                      
00abd169 mov      rax, qword ptr [rip + 0x52fa2d8]              
00abd170 mov      rax, qword ptr [rax + 0xb8]                   
00abd177 mov      rcx, qword ptr [rax + 0x70]                   
00abd17b test     rcx, rcx                                      
00abd17e je       0xabf595                                      
00abd184 mov      rcx, qword ptr [rcx + 0x50]                   
00abd188 test     rcx, rcx                                      
00abd18b je       0xabf595                                      
00abd191 xor      edx, edx                                      
00abd193 call     0x8981f0                                      System.Boolean UIGame::get_IsFocused()
00abd198 mov      r13d, 1                                       
00abd19e test     al, al                                        
00abd1a0 jne      0xabd6c1                                      
00abd1a6 xor      ecx, ecx                                      
00abd1a8 mov      qword ptr [rsp + 0x40], r12                   
00abd1ad call     0x83ca10                                      
00abd1b2 test     eax, eax                                      
00abd1b4 jne      0xabd22c                                      
00abd1b6 xor      edx, edx                                      
00abd1b8 lea      ecx, [rax + 0x29]                             
00abd1bb call     0xaa9250                                      System.Boolean HotkeyManager::GetKey(Hotkey)
00abd1c0 xor      edx, edx                                      
00abd1c2 movzx    r14d, al                                      
00abd1c6 lea      ecx, [rdx + 0x2b]                             
00abd1c9 call     0xaa9250                                      System.Boolean HotkeyManager::GetKey(Hotkey)
00abd1ce xor      edx, edx                                      
00abd1d0 movzx    ebx, al                                       
00abd1d3 lea      ecx, [rdx + 0x28]                             
00abd1d6 call     0xaa9250                                      System.Boolean HotkeyManager::GetKey(Hotkey)
00abd1db xor      edx, edx                                      
00abd1dd movzx    esi, al                                       
00abd1e0 lea      ecx, [rdx + 0x2a]                             
00abd1e3 call     0xaa9250                                      System.Boolean HotkeyManager::GetKey(Hotkey)
00abd1e8 lea      r9, [r15 + 0x310]                             
00abd1ef mov      qword ptr [rsp + 0x20], r12                   
00abd1f4 movzx    r8d, bl                                       
00abd1f8 movzx    edx, r14b                                     
00abd1fc mov      rcx, r15                                      
00abd1ff movzx    edi, al                                       
00abd202 call     0xad7ad0                                      System.Single PlayerController::ResolveAxis(System.Boolean,System.Boolean,System.Int32&)
00abd207 lea      r9, [r15 + 0x314]                             
00abd20e mov      qword ptr [rsp + 0x20], r12                   
00abd213 movzx    r8d, sil                                      
00abd217 movzx    edx, dil                                      
00abd21b mov      rcx, r15                                      
00abd21e movaps   xmm8, xmm0                                    
00abd222 call     0xad7ad0                                      System.Single PlayerController::ResolveAxis(System.Boolean,System.Boolean,System.Int32&)
00abd227 movaps   xmm6, xmm0                                    
00abd22a jmp      0xabd259                                      
00abd22c cmp      eax, r13d                                     
00abd22f jne      0xabd24c                                      
00abd231 xor      ecx, ecx                                      
00abd233 call     0xaa8a90                                      UnityEngine.Vector2 HotkeyManager::GetJoystickLeft()
00abd238 mov      qword ptr [rsp + 0x60], rax                   
00abd23d movss    xmm8, dword ptr [rsp + 0x60]                  
00abd244 movss    xmm6, dword ptr [rsp + 0x64]                  
00abd24a jmp      0xabd259                                      
00abd24c movss    xmm6, dword ptr [rsp + 0x44]                  
00abd252 movss    xmm8, dword ptr [rsp + 0x40]                  
00abd259 mov      rax, qword ptr [rip + 0x52fa1e8]              
00abd260 cmp      dword ptr [rax + 0xe4], r12d                  
00abd267 jne      0xabd278                                      
00abd269 mov      rcx, rax                                      
00abd26c call     0x580d30                                      
00abd271 mov      rax, qword ptr [rip + 0x52fa1d0]              
00abd278 mov      rax, qword ptr [rax + 0xb8]                   
00abd27f mov      rbx, qword ptr [rax + 0x60]                   
00abd283 test     rbx, rbx                                      
00abd286 je       0xabf595                                      
00abd28c mov      rbx, qword ptr [rbx + 0x40]                   
00abd290 test     rbx, rbx                                      
00abd293 je       0xabf595                                      
00abd299 xor      edx, edx                                      
00abd29b mov      rcx, rbx                                      
00abd29e call     0x44204d0                                     
00abd2a3 test     rax, rax                                      
00abd2a6 je       0xabf595                                      
00abd2ac xor      r8d, r8d                                      
00abd2af lea      rcx, [rsp + 0x30]                             
00abd2b4 mov      rdx, rax                                      
00abd2b7 call     0x4452ac0                                     
00abd2bc movsd    xmm0, qword ptr [rax]                         
00abd2c0 movss    xmm10, dword ptr [rax + 8]                    
00abd2c6 movaps   xmm7, xmm0                                    
00abd2c9 shufps   xmm7, xmm7, 0x55                              
00abd2cd movaps   xmm9, xmm0                                    
00abd2d1 mulss    xmm7, xmm6                                    
00abd2d5 mulss    xmm9, xmm6                                    
00abd2da movsd    qword ptr [rsp + 0x60], xmm0                  
00abd2e0 mulss    xmm10, xmm6                                   
00abd2e5 xor      edx, edx                                      
00abd2e7 mov      rcx, rbx                                      
00abd2ea call     0x44204d0                                     
00abd2ef test     rax, rax                                      
00abd2f2 je       0xabf595                                      
00abd2f8 xor      r8d, r8d                                      
00abd2fb lea      rcx, [rsp + 0x30]                             
00abd300 mov      rdx, rax                                      
00abd303 call     0x4453440                                     
00abd308 movsd    xmm0, qword ptr [rax]                         
00abd30c movaps   xmm1, xmm0                                    
00abd30f movsd    qword ptr [rsp + 0x60], xmm0                  
00abd315 movaps   xmm2, xmm0                                    
00abd318 shufps   xmm1, xmm1, 0x55                              
00abd31c movss    xmm0, dword ptr [rax + 8]                     
00abd321 mulss    xmm1, xmm8                                    
00abd326 mulss    xmm2, xmm8                                    
00abd32b mulss    xmm0, xmm8                                    
00abd330 addss    xmm2, xmm9                                    
00abd335 addss    xmm1, xmm7                                    
00abd339 addss    xmm0, xmm10                                   
00abd33e cmp      byte ptr [rip + 0x56add12], r12b              
00abd345 movss    dword ptr [rsp + 0x40], xmm2                  
00abd34b movss    dword ptr [rsp + 0x44], xmm1                  
00abd351 movss    dword ptr [rsp + 0x48], xmm0                  
00abd357 jne      0xabd36c                                      
00abd359 lea      rcx, [rip + 0x5278bf0]                        
00abd360 call     0x5809f0                                      
00abd365 mov      byte ptr [rip + 0x56adceb], r13b              
00abd36c mov      rax, qword ptr [rip + 0x5278bdd]              
00abd373 lea      r8, [rsp + 0x60]                              
00abd378 xor      r9d, r9d                                      
00abd37b lea      rdx, [rsp + 0x30]                             
00abd380 lea      rcx, [rsp + 0x50]                             
00abd385 mov      rax, qword ptr [rax + 0xb8]                   
00abd38c movsd    xmm0, qword ptr [rax + 0x18]                  
00abd391 mov      eax, dword ptr [rax + 0x20]                   
00abd394 movsd    qword ptr [rsp + 0x60], xmm0                  
00abd39a movsd    xmm0, qword ptr [rsp + 0x40]                  
00abd3a0 mov      dword ptr [rsp + 0x68], eax                   
00abd3a4 mov      eax, dword ptr [rsp + 0x48]                   
00abd3a8 movsd    qword ptr [rsp + 0x30], xmm0                  
00abd3ae mov      dword ptr [rsp + 0x38], eax                   
00abd3b2 call     0xaba070                                      
00abd3b7 xor      r8d, r8d                                      
00abd3ba lea      rdx, [rsp + 0x40]                             
00abd3bf lea      rcx, [rsp + 0x50]                             
00abd3c4 movsd    xmm0, qword ptr [rax]                         
00abd3c8 mov      eax, dword ptr [rax + 8]                      
00abd3cb movsd    qword ptr [rsp + 0x40], xmm0                  
00abd3d1 mov      dword ptr [rsp + 0x48], eax                   
00abd3d5 call     0x6c76b0                                      
00abd3da mov      rcx, qword ptr [rip + 0x52bcfb7]              
00abd3e1 movsd    xmm6, qword ptr [rax]                         
00abd3e5 mov      ebx, dword ptr [rax + 8]                      
00abd3e8 cmp      dword ptr [rcx + 0xe4], r12d                  
00abd3ef jne      0xabd3f6                                      
00abd3f1 call     0x580d30                                      
00abd3f6 xor      r8d, r8d                                      
00abd3f9 movsd    qword ptr [rsp + 0x30], xmm6                  
00abd3ff lea      rdx, [rsp + 0x30]                             
00abd404 mov      dword ptr [rsp + 0x38], ebx                   
00abd408 lea      rcx, [rsp + 0x50]                             
00abd40d call     0x7f8040                                      UnityEngine.Vector3Int Extensions::CompressV3(UnityEngine.Vector3)
00abd412 mov      ebx, r12d                                     
00abd415 mov      edx, r12d                                     
00abd418 mov      ecx, dword ptr [rax + 8]                      
00abd41b movsd    xmm0, qword ptr [rax]                         
00abd41f movsd    qword ptr [r15 + 0x328], xmm0                 
00abd428 mov      dword ptr [r15 + 0x330], ecx                  
00abd42f mov      qword ptr [r15 + 0x388], r12                  
00abd436 mov      qword ptr [r15 + 0x390], r12                  
00abd43d mov      rax, qword ptr [rip + 0x52dfe7c]              
00abd444 mov      rcx, qword ptr [rax + 0xb8]                   
00abd44b mov      rax, qword ptr [rcx + 0x18]                   
00abd44f test     rax, rax                                      
00abd452 je       0xabf595                                      
00abd458 nop      dword ptr [rax + rax]                         
00abd460 cmp      edx, dword ptr [rax + 0x18]                   
00abd463 jge      0xabd504                                      
00abd469 xor      r8d, r8d                                      
00abd46c lea      rcx, [rsp + 0x50]                             
00abd471 mov      edx, ebx                                      
00abd473 call     0xaa9320                                      HotkeyBinding HotkeyManager::Get(Hotkey)
00abd478 xor      edx, edx                                      
00abd47a lea      rcx, [rsp + 0x78]                             
00abd47f movups   xmm0, xmmword ptr [rax]                       
00abd482 movups   xmmword ptr [rsp + 0x78], xmm0                
00abd487 call     0xaa7a30                                      System.Boolean HotkeyBinding::HasModifier()
00abd48c test     al, al                                        
00abd48e jne      0xabd4a0                                      
00abd490 xor      edx, edx                                      
00abd492 lea      rcx, [rsp + 0x78]                             
00abd497 call     0xaa7ab0                                      System.Boolean HotkeyBinding::IsModifier()
00abd49c test     al, al                                        
00abd49e je       0xabd4e0                                      
00abd4a0 xor      edx, edx                                      
00abd4a2 mov      ecx, ebx                                      
00abd4a4 call     0xaa91e0                                      System.Boolean HotkeyManager::GetKeyDown(Hotkey)
00abd4a9 xor      r9d, r9d                                      
00abd4ac lea      rcx, [r15 + 0x328]                            
00abd4b3 movzx    r8d, al                                       
00abd4b7 mov      edx, ebx                                      
00abd4b9 call     0x715e40                                      System.Void PlayerInputDto::SetHotkey(Hotkey,System.Boolean)
00abd4be xor      r8d, r8d                                      
00abd4c1 mov      edx, ebx                                      
00abd4c3 mov      rcx, r15                                      
00abd4c6 call     0xac9210                                      System.Boolean PlayerController::IsKeyHeld(Hotkey)
00abd4cb xor      r9d, r9d                                      
00abd4ce lea      rcx, [r15 + 0x328]                            
00abd4d5 movzx    r8d, al                                       
00abd4d9 mov      edx, ebx                                      
00abd4db call     0x715e10                                      System.Void PlayerInputDto::SetHotkeyHeld(Hotkey,System.Boolean)
00abd4e0 mov      rax, qword ptr [rip + 0x52dfdd9]              
00abd4e7 inc      ebx                                           
00abd4e9 mov      edx, ebx                                      
00abd4eb mov      rcx, qword ptr [rax + 0xb8]                   
00abd4f2 mov      rax, qword ptr [rcx + 0x18]                   
00abd4f6 test     rax, rax                                      
00abd4f9 je       0xabf595                                      
00abd4ff jmp      0xabd460                                      
00abd504 xor      ecx, ecx                                      
00abd506 call     0xaaaac0                                      System.Boolean HotkeyManager::get_IsShift()
00abd50b test     al, al                                        
00abd50d jne      0xabd56c                                      
00abd50f xor      ecx, ecx                                      
00abd511 call     0xaaa8b0                                      System.Boolean HotkeyManager::get_IsAlt()
00abd516 test     al, al                                        
00abd518 jne      0xabd56c                                      
00abd51a xor      ecx, ecx                                      
00abd51c call     0xaaa930                                      System.Boolean HotkeyManager::get_IsCtrl()
00abd521 test     al, al                                        
00abd523 jne      0xabd56c                                      
00abd525 xor      edx, edx                                      
00abd527 lea      ecx, [rdx + 6]                                
00abd52a call     0xaa8a50                                      System.Boolean HotkeyManager::GetGamepadKey(HotkeyGamepad)
00abd52f test     al, al                                        
00abd531 jne      0xabd56c                                      
00abd533 xor      edx, edx                                      
00abd535 lea      ecx, [rdx + 4]                                
00abd538 call     0xaa8a50                                      System.Boolean HotkeyManager::GetGamepadKey(HotkeyGamepad)
00abd53d test     al, al                                        
00abd53f jne      0xabd56c                                      
00abd541 xor      edx, edx                                      
00abd543 lea      ecx, [rdx + 7]                                
00abd546 call     0xaa8a50                                      System.Boolean HotkeyManager::GetGamepadKey(HotkeyGamepad)
00abd54b test     al, al                                        
00abd54d jne      0xabd56c                                      
00abd54f xor      edx, edx                                      
00abd551 lea      ecx, [rdx + 5]                                
00abd554 call     0xaa8a50                                      System.Boolean HotkeyManager::GetGamepadKey(HotkeyGamepad)
00abd559 movzx    ebx, al                                       
00abd55c test     al, al                                        
00abd55e jne      0xabd56f                                      
00abd560 mov      rcx, qword ptr [rip + 0x52dfd59]              
00abd567 xor      dil, dil                                      
00abd56a jmp      0xabd5b3                                      
00abd56c mov      ebx, r13d                                     
00abd56f cmp      byte ptr [rip + 0x56ae870], r12b              
00abd576 jne      0xabd58b                                      
00abd578 lea      rcx, [rip + 0x52dfd41]                        
00abd57f call     0x5809f0                                      
00abd584 mov      byte ptr [rip + 0x56ae85b], r13b              
00abd58b mov      rcx, qword ptr [rip + 0x52dfd2e]              
00abd592 mov      rax, qword ptr [rcx + 0xb8]                   
00abd599 cmp      dword ptr [rax + 0x28], r13d                  
00abd59d sete     dil                                           
00abd5a1 test     ebx, ebx                                      
00abd5a3 movzx    eax, dil                                      
00abd5a7 cmove    eax, r13d                                     
00abd5ab test     eax, eax                                      
00abd5ad je       0xabd683                                      
00abd5b3 mov      rax, qword ptr [rcx + 0xb8]                   
00abd5ba mov      ebx, r12d                                     
00abd5bd mov      edx, r12d                                     
00abd5c0 mov      rcx, qword ptr [rax + 0x18]                   
00abd5c4 test     rcx, rcx                                      
00abd5c7 je       0xabf595                                      
00abd5cd nop      dword ptr [rax]                               
00abd5d0 cmp      edx, dword ptr [rcx + 0x18]                   
00abd5d3 jge      0xabd683                                      
00abd5d9 xor      r8d, r8d                                      
00abd5dc lea      rcx, [rsp + 0x50]                             
00abd5e1 mov      edx, ebx                                      
00abd5e3 call     0xaa9320                                      HotkeyBinding HotkeyManager::Get(Hotkey)
00abd5e8 xor      edx, edx                                      
00abd5ea lea      rcx, [rbp - 0x78]                             
00abd5ee movups   xmm0, xmmword ptr [rax]                       
00abd5f1 movups   xmmword ptr [rbp - 0x78], xmm0                
00abd5f5 call     0xaa7a30                                      System.Boolean HotkeyBinding::HasModifier()
00abd5fa test     al, al                                        
00abd5fc jne      0xabd65f                                      
00abd5fe xor      edx, edx                                      
00abd600 lea      rcx, [rbp - 0x78]                             
00abd604 call     0xaa7ab0                                      System.Boolean HotkeyBinding::IsModifier()
00abd609 test     al, al                                        
00abd60b jne      0xabd65f                                      
00abd60d test     dil, dil                                      
00abd610 je       0xabd61f                                      
00abd612 xor      edx, edx                                      
00abd614 mov      ecx, ebx                                      
00abd616 call     0xaa93a0                                      System.Boolean HotkeyManager::IsBaseKeyClaimedByModifier(Hotkey)
00abd61b test     al, al                                        
00abd61d jne      0xabd65f                                      
00abd61f xor      edx, edx                                      
00abd621 mov      ecx, ebx                                      
00abd623 call     0xaa91e0                                      System.Boolean HotkeyManager::GetKeyDown(Hotkey)
00abd628 xor      r9d, r9d                                      
00abd62b lea      rcx, [r15 + 0x328]                            
00abd632 movzx    r8d, al                                       
00abd636 mov      edx, ebx                                      
00abd638 call     0x715e40                                      System.Void PlayerInputDto::SetHotkey(Hotkey,System.Boolean)
00abd63d xor      r8d, r8d                                      
00abd640 mov      edx, ebx                                      
00abd642 mov      rcx, r15                                      
00abd645 call     0xac9210                                      System.Boolean PlayerController::IsKeyHeld(Hotkey)
00abd64a xor      r9d, r9d                                      
00abd64d lea      rcx, [r15 + 0x328]                            
00abd654 movzx    r8d, al                                       
00abd658 mov      edx, ebx                                      
00abd65a call     0x715e10                                      System.Void PlayerInputDto::SetHotkeyHeld(Hotkey,System.Boolean)
00abd65f mov      rax, qword ptr [rip + 0x52dfc5a]              
00abd666 inc      ebx                                           
00abd668 mov      edx, ebx                                      
00abd66a mov      rcx, qword ptr [rax + 0xb8]                   
00abd671 mov      rcx, qword ptr [rcx + 0x18]                   
00abd675 test     rcx, rcx                                      
00abd678 jne      0xabd5d0                                      
00abd67e jmp      0xabf595                                      
00abd683 mov      rax, qword ptr [rip + 0x52f160e]              
00abd68a cmp      dword ptr [rax + 0xe4], r12d                  
00abd691 jne      0xabd6a2                                      
00abd693 mov      rcx, rax                                      
00abd696 call     0x580d30                                      
00abd69b mov      rax, qword ptr [rip + 0x52f15f6]              
00abd6a2 mov      rax, qword ptr [rax + 0xb8]                   
00abd6a9 mov      rax, qword ptr [rax + 0x78]                   
00abd6ad test     rax, rax                                      
00abd6b0 je       0xabf595                                      
00abd6b6 movzx    eax, byte ptr [rax + 0x10]                    
00abd6ba mov      byte ptr [r15 + 0x381], al                    
00abd6c1 xor      edx, edx                                      
00abd6c3 mov      rcx, r15                                      
00abd6c6 call     0xaed530                                      System.Void PlayerController::SampleTargets()
00abd6cb mov      rax, qword ptr [rip + 0x52f9d76]              
00abd6d2 cmp      dword ptr [rax + 0xe4], r12d                  
00abd6d9 jne      0xabd6ea                                      
00abd6db mov      rcx, rax                                      
00abd6de call     0x580d30                                      
00abd6e3 mov      rax, qword ptr [rip + 0x52f9d5e]              
00abd6ea mov      rax, qword ptr [rax + 0xb8]                   
00abd6f1 mov      rax, qword ptr [rax + 0x70]                   
00abd6f5 test     rax, rax                                      
00abd6f8 je       0xabf595                                      
00abd6fe mov      rax, qword ptr [rax + 0x50]                   
00abd702 test     rax, rax                                      
00abd705 je       0xabf595                                      
00abd70b mov      rcx, qword ptr [rax + 0x150]                  
00abd712 test     rcx, rcx                                      
00abd715 je       0xabf595                                      
00abd71b mov      rbx, qword ptr [rcx + 0xc8]                   
00abd722 mov      rcx, qword ptr [rip + 0x529e917]              
00abd729 cmp      dword ptr [rcx + 0xe4], r12d                  
00abd730 jne      0xabd737                                      
00abd732 call     0x580d30                                      
00abd737 xor      r8d, r8d                                      
00abd73a xor      edx, edx                                      
00abd73c mov      rcx, rbx                                      
00abd73f call     0x443db80                                     
00abd744 mov      ebx, r12d                                     
00abd747 test     al, al                                        
00abd749 je       0xabd755                                      
00abd74b cmp      qword ptr [r15 + 0x438], rbx                  
00abd752 seta     bl                                            
00abd755 mov      rcx, qword ptr [rip + 0x529e8e4]              
00abd75c mov      rdi, qword ptr [r15 + 0x2e0]                  
00abd763 cmp      dword ptr [rcx + 0xe4], r12d                  
00abd76a jne      0xabd771                                      
00abd76c call     0x580d30                                      
00abd771 xor      edx, edx                                      
00abd773 mov      rcx, rdi                                      
00abd776 call     0x443daf0                                     
00abd77b test     al, al                                        
00abd77d jne      0xabd837                                      
00abd783 mov      rcx, qword ptr [rip + 0x529e8b6]              
00abd78a mov      rdi, qword ptr [r15 + 0x2e8]                  
00abd791 cmp      dword ptr [rcx + 0xe4], r12d                  
00abd798 jne      0xabd79f                                      
00abd79a call     0x580d30                                      
00abd79f xor      edx, edx                                      
00abd7a1 mov      rcx, rdi                                      
00abd7a4 call     0x443daf0                                     
00abd7a9 test     al, al                                        
00abd7ab mov      rax, qword ptr [rip + 0x52f9c96]              
00abd7b2 jne      0xabd7f5                                      
00abd7b4 cmp      dword ptr [rax + 0xe4], r12d                  
00abd7bb jne      0xabd7cc                                      
00abd7bd mov      rcx, rax                                      
00abd7c0 call     0x580d30                                      
00abd7c5 mov      rax, qword ptr [rip + 0x52f9c7c]              
00abd7cc mov      rax, qword ptr [rax + 0xb8]                   
00abd7d3 mov      rcx, qword ptr [rax + 0x70]                   
00abd7d7 test     rcx, rcx                                      
00abd7da je       0xabf595                                      
00abd7e0 mov      rcx, qword ptr [rcx + 0x50]                   
00abd7e4 test     rcx, rcx                                      
00abd7e7 je       0xabf595                                      
00abd7ed mov      rdx, r12                                      
00abd7f0 jmp      0xabd87e                                      
00abd7f5 cmp      dword ptr [rax + 0xe4], r12d                  
00abd7fc jne      0xabd80d                                      
00abd7fe mov      rcx, rax                                      
00abd801 call     0x580d30                                      
00abd806 mov      rax, qword ptr [rip + 0x52f9c3b]              
00abd80d mov      rax, qword ptr [rax + 0xb8]                   
00abd814 mov      rcx, qword ptr [rax + 0x70]                   
00abd818 test     rcx, rcx                                      
00abd81b je       0xabf595                                      
00abd821 mov      rcx, qword ptr [rcx + 0x50]                   
00abd825 test     rcx, rcx                                      
00abd828 je       0xabf595                                      
00abd82e mov      rdx, qword ptr [r15 + 0x2e8]                  
00abd835 jmp      0xabd87e                                      
00abd837 mov      rax, qword ptr [rip + 0x52f9c0a]              
00abd83e cmp      dword ptr [rax + 0xe4], r12d                  
00abd845 jne      0xabd856                                      
00abd847 mov      rcx, rax                                      
00abd84a call     0x580d30                                      
00abd84f mov      rax, qword ptr [rip + 0x52f9bf2]              
00abd856 mov      rax, qword ptr [rax + 0xb8]                   
00abd85d mov      rcx, qword ptr [rax + 0x70]                   
00abd861 test     rcx, rcx                                      
00abd864 je       0xabf595                                      
00abd86a mov      rcx, qword ptr [rcx + 0x50]                   
00abd86e test     rcx, rcx                                      
00abd871 je       0xabf595                                      
00abd877 mov      rdx, qword ptr [r15 + 0x2e0]                  
00abd87e xor      r8d, r8d                                      
00abd881 call     0x897890                                      System.Void UIGame::SetTempTarget(BaseUnitController)
00abd886 xor      r8d, r8d                                      
00abd889 lea      rcx, [r15 + 0x328]                            
00abd890 lea      edx, [r8 + 0x30]                              
00abd894 call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abd899 test     al, al                                        
00abd89b jne      0xabd8b4                                      
00abd89d xor      r8d, r8d                                      
00abd8a0 lea      rcx, [r15 + 0x328]                            
00abd8a7 lea      edx, [r8 + 0x30]                              
00abd8ab call     0x715dd0                                      System.Boolean PlayerInputDto::GetHotkeyHeld(Hotkey)
00abd8b0 test     al, al                                        
00abd8b2 je       0xabd90e                                      
00abd8b4 mov      rcx, qword ptr [rip + 0x529e785]              
00abd8bb mov      rdi, qword ptr [r15 + 0x2e0]                  
00abd8c2 cmp      dword ptr [rcx + 0xe4], r12d                  
00abd8c9 jne      0xabd8d0                                      
00abd8cb call     0x580d30                                      
00abd8d0 xor      edx, edx                                      
00abd8d2 mov      rcx, rdi                                      
00abd8d5 call     0x443daf0                                     
00abd8da test     al, al                                        
00abd8dc je       0xabd90e                                      
00abd8de mov      rcx, qword ptr [r15 + 0x2e0]                  
00abd8e5 test     rcx, rcx                                      
00abd8e8 je       0xabf595                                      
00abd8ee xor      edx, edx                                      
00abd8f0 call     0xc22560                                      
00abd8f5 mov      dword ptr [r15 + 0x36c], eax                  
00abd8fc xor      r8d, r8d                                      
00abd8ff mov      rdx, qword ptr [r15 + 0x2e0]                  
00abd906 mov      rcx, r15                                      
00abd909 call     0xad2a30                                      System.Boolean PlayerController::ProcessClickedUnit(BaseUnitController)
00abd90e mov      rcx, qword ptr [rip + 0x52f9b33]              
00abd915 cmp      dword ptr [rcx + 0xe4], r12d                  
00abd91c jne      0xabd92a                                      
00abd91e call     0x580d30                                      
00abd923 mov      rcx, qword ptr [rip + 0x52f9b1e]              
00abd92a mov      rax, qword ptr [rcx + 0xb8]                   
00abd931 mov      rdx, qword ptr [rax + 0x60]                   
00abd935 test     rdx, rdx                                      
00abd938 je       0xabf595                                      
00abd93e cmp      byte ptr [rdx + 0xa1], r12b                   
00abd945 cmove    ebx, r13d                                     
00abd949 test     ebx, ebx                                      
00abd94b jne      0xabd99c                                      
00abd94d cmp      dword ptr [rcx + 0xe4], r12d                  
00abd954 jne      0xabd962                                      
00abd956 call     0x580d30                                      
00abd95b mov      rcx, qword ptr [rip + 0x52f9ae6]              
00abd962 mov      rax, qword ptr [rcx + 0xb8]                   
00abd969 mov      rax, qword ptr [rax + 0x70]                   
00abd96d test     rax, rax                                      
00abd970 je       0xabf595                                      
00abd976 mov      rax, qword ptr [rax + 0x50]                   
00abd97a test     rax, rax                                      
00abd97d je       0xabf595                                      
00abd983 mov      rcx, qword ptr [rax + 0x28]                   
00abd987 test     rcx, rcx                                      
00abd98a je       0xabf595                                      
00abd990 xor      edx, edx                                      
00abd992 call     0x8bb370                                      System.Void UITargetIndicator::Hide()
00abd997 jmp      0xabe985                                      
00abd99c cmp      byte ptr [rip + 0x56ae443], r12b              
00abd9a3 jne      0xabd9b8                                      
00abd9a5 lea      rcx, [rip + 0x52df914]                        
00abd9ac call     0x5809f0                                      
00abd9b1 mov      byte ptr [rip + 0x56ae42e], r13b              
00abd9b8 mov      rax, qword ptr [rip + 0x52df901]              
00abd9bf mov      rcx, qword ptr [rax + 0xb8]                   
00abd9c6 cmp      dword ptr [rcx + 0x28], r13d                  
00abd9ca je       0xabd9d1                                      
00abd9cc xor      r14b, r14b                                    
00abd9cf jmp      0xabd9e8                                      
00abd9d1 xor      r8d, r8d                                      
00abd9d4 lea      rcx, [r15 + 0x328]                            
00abd9db lea      edx, [r8 + 0x2c]                              
00abd9df call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abd9e4 movzx    r14d, al                                      
00abd9e8 xor      edx, edx                                      
00abd9ea mov      ecx, 0x143                                    
00abd9ef call     0x44d2110                                     
00abd9f4 or       al, r14b                                      
00abd9f7 xor      edx, edx                                      
00abd9f9 mov      ecx, 0x144                                    
00abd9fe mov      byte ptr [r15 + 0x364], al                    
00abda05 call     0x44d2190                                     
00abda0a mov      byte ptr [r15 + 0x365], al                    
00abda11 cmp      qword ptr [r15 + 0x438], r12                  
00abda18 jne      0xabde87                                      
00abda1e mov      rcx, qword ptr [rip + 0x529e61b]              
00abda25 mov      rbx, qword ptr [r15 + 0x2e0]                  
00abda2c cmp      dword ptr [rcx + 0xe4], r12d                  
00abda33 jne      0xabda3a                                      
00abda35 call     0x580d30                                      
00abda3a xor      edx, edx                                      
00abda3c mov      rcx, rbx                                      
00abda3f call     0x443daf0                                     
00abda44 test     al, al                                        
00abda46 jne      0xabdca8                                      
00abda4c mov      rcx, qword ptr [rip + 0x529e5ed]              
00abda53 mov      rbx, qword ptr [r15 + 0x2e8]                  
00abda5a cmp      dword ptr [rcx + 0xe4], r12d                  
00abda61 jne      0xabda68                                      
00abda63 call     0x580d30                                      
00abda68 xor      edx, edx                                      
00abda6a mov      rcx, rbx                                      
00abda6d call     0x443daf0                                     
00abda72 test     al, al                                        
00abda74 mov      rax, qword ptr [rip + 0x52f99cd]              
00abda7b jne      0xabdbee                                      
00abda81 cmp      qword ptr [r15 + 0x2f0], r12                  
00abda88 je       0xabe273                                      
00abda8e cmp      dword ptr [rax + 0xe4], r12d                  
00abda95 jne      0xabdaa6                                      
00abda97 mov      rcx, rax                                      
00abda9a call     0x580d30                                      
00abda9f mov      rax, qword ptr [rip + 0x52f99a2]              
00abdaa6 mov      rax, qword ptr [rax + 0xb8]                   
00abdaad mov      rax, qword ptr [rax + 0x70]                   
00abdab1 test     rax, rax                                      
00abdab4 je       0xabf595                                      
00abdaba mov      rax, qword ptr [rax + 0x50]                   
00abdabe test     rax, rax                                      
00abdac1 je       0xabf595                                      
00abdac7 mov      r8, qword ptr [r15 + 0x2f0]                   
00abdace mov      rdi, qword ptr [rax + 0x28]                   
00abdad2 test     r8, r8                                        
00abdad5 je       0xabf595                                      
00abdadb mov      rdx, qword ptr [rip + 0x52f93be]              
00abdae2 mov      ecx, 2                                        
00abdae7 call     0x30d0                                        
00abdaec mov      rbx, qword ptr [r15 + 0x2f0]                  
00abdaf3 mov      rsi, rax                                      
00abdaf6 test     rbx, rbx                                      
00abdaf9 je       0xabf595                                      
00abdaff mov      r10, qword ptr [rbx]                          
00abdb02 movzx    ecx, r12w                                     
00abdb06 mov      r9, qword ptr [rip + 0x52f9393]               
00abdb0d movzx    edx, word ptr [r10 + 0x12e]                   
00abdb15 cmp      r12w, dx                                      
00abdb19 jae      0xabdb48                                      
00abdb1b mov      r8, qword ptr [r10 + 0xb0]                    
00abdb22 nop      dword ptr [rax]                               
00abdb26 nop      word ptr [rax + rax]                          
00abdb30 movzx    eax, cx                                       
00abdb33 add      rax, rax                                      
00abdb36 cmp      qword ptr [r8 + rax*8], r9                    
00abdb3a je       0xabdbd1                                      
00abdb40 inc      cx                                            
00abdb43 cmp      cx, dx                                        
00abdb46 jb       0xabdb30                                      
00abdb48 xor      r8d, r8d                                      
00abdb4b mov      rdx, r9                                       
00abdb4e mov      rcx, rbx                                      
00abdb51 call     0x57dd50                                      
00abdb56 mov      r8, qword ptr [rax]                           
00abdb59 mov      rcx, rbx                                      
00abdb5c mov      rdx, qword ptr [rax + 8]                      
00abdb60 call     r8                                            
00abdb63 test     rdi, rdi                                      
00abdb66 je       0xabf595                                      
00abdb6c movss    xmm3, dword ptr [rip + 0x3e53f74]             
00abdb74 mov      r8, rax                                       
00abdb77 mov      rdx, rsi                                      
00abdb7a mov      qword ptr [rsp + 0x20], r12                   
00abdb7f mov      rcx, rdi                                      
00abdb82 call     0x8bac40                                      UITargetIndicator UITargetIndicator::Draw(UnityEngine.GameObject,System.String,System.Single)
00abdb87 mov      r8, qword ptr [r15 + 0x2f0]                   
00abdb8e mov      rbx, rax                                      
00abdb91 test     r8, r8                                        
00abdb94 je       0xabf595                                      
00abdb9a mov      rdx, qword ptr [rip + 0x52f92ff]              
00abdba1 mov      ecx, r13d                                     
00abdba4 call     0x169f0                                       
00abdba9 test     rbx, rbx                                      
00abdbac je       0xabf595                                      
00abdbb2 mulss    xmm0, dword ptr [rip + 0x3e53f2a]             
00abdbba xor      r9d, r9d                                      
00abdbbd movzx    r8d, r13b                                     
00abdbc1 mov      rcx, rbx                                      
00abdbc4 movaps   xmm1, xmm0                                    
00abdbc7 call     0x8bbb60                                      UITargetIndicator UITargetIndicator::SetIndicator(System.Single,System.Boolean)
00abdbcc jmp      0xabe2c0                                      
00abdbd1 movzx    ecx, cx                                       
00abdbd4 add      rcx, rcx                                      
00abdbd7 movsxd   rax, dword ptr [r8 + rcx*8 + 8]               
00abdbdc shl      rax, 4                                        
00abdbe0 add      rax, 0x138                                    
00abdbe6 add      rax, r10                                      
00abdbe9 jmp      0xabdb56                                      
00abdbee cmp      dword ptr [rax + 0xe4], r12d                  
00abdbf5 jne      0xabdc06                                      
00abdbf7 mov      rcx, rax                                      
00abdbfa call     0x580d30                                      
00abdbff mov      rax, qword ptr [rip + 0x52f9842]              
00abdc06 mov      rax, qword ptr [rax + 0xb8]                   
00abdc0d mov      rcx, qword ptr [rax + 0x70]                   
00abdc11 test     rcx, rcx                                      
00abdc14 je       0xabf595                                      
00abdc1a mov      rax, qword ptr [rcx + 0x50]                   
00abdc1e test     rax, rax                                      
00abdc21 je       0xabf595                                      
00abdc27 mov      rcx, qword ptr [rax + 0x28]                   
00abdc2b xorps    xmm0, xmm0                                    
00abdc2e test     rcx, rcx                                      
00abdc31 je       0xabf595                                      
00abdc37 mov      rdx, qword ptr [r15 + 0x2e8]                  
00abdc3e lea      r8, [rsp + 0x50]                              
00abdc43 xor      r9d, r9d                                      
00abdc46 movdqa   xmmword ptr [rsp + 0x50], xmm0                
00abdc4c mov      qword ptr [rsp + 0x20], r12                   
00abdc51 call     0x8bacc0                                      UITargetIndicator UITargetIndicator::Draw(BaseUnitController,UnityEngine.Color,Formula/Advantage)
00abdc56 mov      rcx, qword ptr [r15 + 0x2e8]                  
00abdc5d mov      rbx, rax                                      
00abdc60 test     rcx, rcx                                      
00abdc63 je       0xabf595                                      
00abdc69 mov      rcx, qword ptr [rcx + 0x128]                  
00abdc70 test     rcx, rcx                                      
00abdc73 je       0xabf595                                      
00abdc79 xor      edx, edx                                      
00abdc7b call     0xaa7380                                      System.Boolean HealthComponent::get_IsAlive()
00abdc80 test     rbx, rbx                                      
00abdc83 je       0xabf595                                      
00abdc89 movss    xmm1, dword ptr [rip + 0x3e530ff]             
00abdc91 xor      al, r13b                                      
00abdc94 movzx    r8d, al                                       
00abdc98 xor      r9d, r9d                                      
00abdc9b mov      rcx, rbx                                      
00abdc9e call     0x8bbb60                                      UITargetIndicator UITargetIndicator::SetIndicator(System.Single,System.Boolean)
00abdca3 jmp      0xabe2c0                                      
00abdca8 cmp      byte ptr [r15 + 0x364], r12b                  
00abdcaf je       0xabdcd4                                      
00abdcb1 test     r14b, r14b                                    
00abdcb4 jne      0xabdcd4                                      
00abdcb6 mov      rcx, qword ptr [r15 + 0x2e0]                  
00abdcbd test     rcx, rcx                                      
00abdcc0 je       0xabf595                                      
00abdcc6 xor      edx, edx                                      
00abdcc8 call     0xc22560                                      
00abdccd mov      dword ptr [r15 + 0x36c], eax                  
00abdcd4 mov      rax, qword ptr [r15 + 0x2e0]                  
00abdcdb test     rax, rax                                      
00abdcde je       0xabf595                                      
00abdce4 mov      rcx, qword ptr [rax + 0x130]                  
00abdceb test     rcx, rcx                                      
00abdcee je       0xabf595                                      
00abdcf4 cmp      byte ptr [rcx + 0x164], r12b                  
00abdcfb jne      0xabde07                                      
00abdd01 mov      rcx, qword ptr [rax + 0x140]                  
00abdd08 test     rcx, rcx                                      
00abdd0b je       0xabf595                                      
00abdd11 mov      rax, qword ptr [rcx + 0x108]                  
00abdd18 test     rax, rax                                      
00abdd1b je       0xabf595                                      
00abdd21 mov      edi, dword ptr [rax + 0x74]                   
00abdd24 mov      rax, qword ptr [r15 + 0x140]                  
00abdd2b test     rax, rax                                      
00abdd2e je       0xabf595                                      
00abdd34 mov      rcx, qword ptr [rax + 0x108]                  
00abdd3b test     rcx, rcx                                      
00abdd3e je       0xabf595                                      
00abdd44 mov      ebx, dword ptr [rcx + 0x74]                   
00abdd47 mov      rcx, qword ptr [rip + 0x52c624a]              
00abdd4e cmp      dword ptr [rcx + 0xe4], r12d                  
00abdd55 jne      0xabdd5c                                      
00abdd57 call     0x580d30                                      
00abdd5c xor      r9d, r9d                                      
00abdd5f lea      rcx, [rsp + 0x50]                             
00abdd64 mov      r8d, ebx                                      
00abdd67 mov      edx, edi                                      
00abdd69 call     0xa44020                                      UnityEngine.Color Formula::GetLevelColoring(System.Int32,System.Int32)
00abdd6e xor      edx, edx                                      
00abdd70 mov      rcx, r15                                      
00abdd73 movups   xmm6, xmmword ptr [rax]                       
00abdd76 call     0xa3f380                                      Element Formula::AttackElement(BaseUnitController)
00abdd7b mov      rcx, qword ptr [r15 + 0x2e0]                  
00abdd82 mov      ebx, eax                                      
00abdd84 test     rcx, rcx                                      
00abdd87 je       0xabf595                                      
00abdd8d mov      rcx, qword ptr [rcx + 0x140]                  
00abdd94 test     rcx, rcx                                      
00abdd97 je       0xabf595                                      
00abdd9d xor      edx, edx                                      
00abdd9f call     0x7e7120                                      Element StatusComponent::GetElement()
00abdda4 xor      r8d, r8d                                      
00abdda7 mov      edx, eax                                      
00abdda9 mov      ecx, ebx                                      
00abddab call     0xa41430                                      Formula/Advantage Formula::GetAdvantage(Element,Element)
00abddb0 mov      rcx, qword ptr [rip + 0x52f9691]              
00abddb7 mov      ebx, eax                                      
00abddb9 cmp      dword ptr [rcx + 0xe4], r12d                  
00abddc0 jne      0xabddce                                      
00abddc2 call     0x580d30                                      
00abddc7 mov      rcx, qword ptr [rip + 0x52f967a]              
00abddce mov      rcx, qword ptr [rcx + 0xb8]                   
00abddd5 mov      rax, qword ptr [rcx + 0x70]                   
00abddd9 test     rax, rax                                      
00abdddc je       0xabf595                                      
00abdde2 mov      rax, qword ptr [rax + 0x50]                   
00abdde6 test     rax, rax                                      
00abdde9 je       0xabf595                                      
00abddef mov      rcx, qword ptr [rax + 0x28]                   
00abddf3 test     rcx, rcx                                      
00abddf6 je       0xabf595                                      
00abddfc movdqa   xmmword ptr [rsp + 0x50], xmm6                
00abde02 mov      r9d, ebx                                      
00abde05 jmp      0xabde6c                                      
00abde07 mov      rcx, qword ptr [rip + 0x52f963a]              
00abde0e cmp      dword ptr [rcx + 0xe4], r12d                  
00abde15 jne      0xabde23                                      
00abde17 call     0x580d30                                      
00abde1c mov      rcx, qword ptr [rip + 0x52f9625]              
00abde23 mov      rax, qword ptr [rcx + 0xb8]                   
00abde2a mov      rdx, qword ptr [rax + 0x70]                   
00abde2e test     rdx, rdx                                      
00abde31 je       0xabf595                                      
00abde37 mov      r8, qword ptr [rdx + 0x50]                    
00abde3b test     r8, r8                                        
00abde3e je       0xabf595                                      
00abde44 mov      rdx, qword ptr [rax]                          
00abde47 test     rdx, rdx                                      
00abde4a je       0xabf595                                      
00abde50 mov      rcx, qword ptr [r8 + 0x28]                    
00abde54 test     rcx, rcx                                      
00abde57 je       0xabf595                                      
00abde5d movups   xmm0, xmmword ptr [rdx + 0x80]                
00abde64 xor      r9d, r9d                                      
00abde67 movaps   xmmword ptr [rsp + 0x50], xmm0                
00abde6c mov      rdx, qword ptr [r15 + 0x2e0]                  
00abde73 lea      r8, [rsp + 0x50]                              
00abde78 mov      qword ptr [rsp + 0x20], r12                   
00abde7d call     0x8bacc0                                      UITargetIndicator UITargetIndicator::Draw(BaseUnitController,UnityEngine.Color,Formula/Advantage)
00abde82 jmp      0xabe2c0                                      
00abde87 mov      rcx, qword ptr [r15 + 0x438]                  
00abde8e test     rcx, rcx                                      
00abde91 je       0xabf595                                      
00abde97 xor      edx, edx                                      
00abde99 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00abde9e test     rax, rax                                      
00abdea1 je       0xabf595                                      
00abdea7 cmp      dword ptr [rax + 0xe4], r13d                  
00abdeae jne      0xabe26c                                      
00abdeb4 mov      rcx, qword ptr [rip + 0x529e185]              
00abdebb mov      rbx, qword ptr [r15 + 0x2e0]                  
00abdec2 cmp      dword ptr [rcx + 0xe4], r12d                  
00abdec9 jne      0xabded0                                      
00abdecb call     0x580d30                                      
00abded0 xor      edx, edx                                      
00abded2 mov      rcx, rbx                                      
00abded5 call     0x443daf0                                     
00abdeda test     al, al                                        
00abdedc je       0xabdff0                                      
00abdee2 mov      rcx, qword ptr [r15 + 0x138]                  
00abdee9 test     rcx, rcx                                      
00abdeec je       0xabf595                                      
00abdef2 mov      r8, qword ptr [r15 + 0x2e0]                   
00abdef9 xor      r9d, r9d                                      
00abdefc mov      rdx, qword ptr [r15 + 0x438]                  
00abdf03 call     0x7b89e0                                      System.Boolean SkillsComponent::CanHit(SkillState,BaseUnitController)
00abdf08 test     al, al                                        
00abdf0a je       0xabdff0                                      
00abdf10 mov      rcx, qword ptr [r15 + 0x2e0]                  
00abdf17 test     rcx, rcx                                      
00abdf1a je       0xabf595                                      
00abdf20 xor      edx, edx                                      
00abdf22 call     0xc22560                                      
00abdf27 mov      dword ptr [r15 + 0x36c], eax                  
00abdf2e mov      rax, qword ptr [r15 + 0x2e0]                  
00abdf35 test     rax, rax                                      
00abdf38 je       0xabf595                                      
00abdf3e mov      rax, qword ptr [rax + 0x140]                  
00abdf45 test     rax, rax                                      
00abdf48 je       0xabf595                                      
00abdf4e mov      rcx, qword ptr [rax + 0x108]                  
00abdf55 test     rcx, rcx                                      
00abdf58 je       0xabf595                                      
00abdf5e mov      rax, qword ptr [r15 + 0x140]                  
00abdf65 mov      edi, dword ptr [rcx + 0x74]                   
00abdf68 test     rax, rax                                      
00abdf6b je       0xabf595                                      
00abdf71 mov      rcx, qword ptr [rax + 0x108]                  
00abdf78 test     rcx, rcx                                      
00abdf7b je       0xabf595                                      
00abdf81 mov      ebx, dword ptr [rcx + 0x74]                   
00abdf84 mov      rcx, qword ptr [rip + 0x52c600d]              
00abdf8b cmp      dword ptr [rcx + 0xe4], r12d                  
00abdf92 jne      0xabdf99                                      
00abdf94 call     0x580d30                                      
00abdf99 xor      r9d, r9d                                      
00abdf9c lea      rcx, [rsp + 0x50]                             
00abdfa1 mov      r8d, ebx                                      
00abdfa4 mov      edx, edi                                      
00abdfa6 call     0xa44020                                      UnityEngine.Color Formula::GetLevelColoring(System.Int32,System.Int32)
00abdfab mov      rcx, qword ptr [r15 + 0x438]                  
00abdfb2 movups   xmm6, xmmword ptr [rax]                       
00abdfb5 test     rcx, rcx                                      
00abdfb8 je       0xabf595                                      
00abdfbe xor      edx, edx                                      
00abdfc0 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00abdfc5 test     rax, rax                                      
00abdfc8 je       0xabf595                                      
00abdfce mov      ebx, dword ptr [rax + 0xdc]                   
00abdfd4 mov      rax, qword ptr [r15 + 0x2e0]                  
00abdfdb test     rax, rax                                      
00abdfde je       0xabf595                                      
00abdfe4 mov      rcx, qword ptr [rax + 0x140]                  
00abdfeb jmp      0xabdd94                                      
00abdff0 mov      rcx, qword ptr [rip + 0x529e049]              
00abdff7 mov      rbx, qword ptr [r15 + 0x2e8]                  
00abdffe cmp      dword ptr [rcx + 0xe4], r12d                  
00abe005 jne      0xabe00c                                      
00abe007 call     0x580d30                                      
00abe00c xor      edx, edx                                      
00abe00e mov      rcx, rbx                                      
00abe011 call     0x443daf0                                     
00abe016 test     al, al                                        
00abe018 je       0xabe0de                                      
00abe01e mov      rcx, qword ptr [r15 + 0x138]                  
00abe025 test     rcx, rcx                                      
00abe028 je       0xabf595                                      
00abe02e mov      r8, qword ptr [r15 + 0x2e8]                   
00abe035 xor      r9d, r9d                                      
00abe038 mov      rdx, qword ptr [r15 + 0x438]                  
00abe03f call     0x7b89e0                                      System.Boolean SkillsComponent::CanHit(SkillState,BaseUnitController)
00abe044 test     al, al                                        
00abe046 je       0xabe0de                                      
00abe04c mov      rcx, qword ptr [r15 + 0x2e8]                  
00abe053 test     rcx, rcx                                      
00abe056 je       0xabf595                                      
00abe05c xor      edx, edx                                      
00abe05e call     0xc22560                                      
00abe063 mov      dword ptr [r15 + 0x36c], eax                  
00abe06a mov      rax, qword ptr [rip + 0x52f93d7]              
00abe071 cmp      dword ptr [rax + 0xe4], r12d                  
00abe078 jne      0xabe089                                      
00abe07a mov      rcx, rax                                      
00abe07d call     0x580d30                                      
00abe082 mov      rax, qword ptr [rip + 0x52f93bf]              
00abe089 mov      rax, qword ptr [rax + 0xb8]                   
00abe090 mov      rcx, qword ptr [rax + 0x70]                   
00abe094 test     rcx, rcx                                      
00abe097 je       0xabf595                                      
00abe09d mov      rax, qword ptr [rcx + 0x50]                   
00abe0a1 test     rax, rax                                      
00abe0a4 je       0xabf595                                      
00abe0aa mov      rcx, qword ptr [rax + 0x28]                   
00abe0ae xorps    xmm0, xmm0                                    
00abe0b1 test     rcx, rcx                                      
00abe0b4 je       0xabf595                                      
00abe0ba mov      rdx, qword ptr [r15 + 0x2e8]                  
00abe0c1 lea      r8, [rsp + 0x50]                              
00abe0c6 xor      r9d, r9d                                      
00abe0c9 movdqa   xmmword ptr [rsp + 0x50], xmm0                
00abe0cf mov      qword ptr [rsp + 0x20], r12                   
00abe0d4 call     0x8bacc0                                      UITargetIndicator UITargetIndicator::Draw(BaseUnitController,UnityEngine.Color,Formula/Advantage)
00abe0d9 jmp      0xabe2c0                                      
00abe0de cmp      byte ptr [rip + 0x56aedcf], r12b              
00abe0e5 mov      rbx, qword ptr [r15 + 0x2f0]                  
00abe0ec jne      0xabe10d                                      
00abe0ee lea      rcx, [rip + 0x52b95bb]                        
00abe0f5 call     0x5809f0                                      
00abe0fa lea      rcx, [rip + 0x52f8d9f]                        
00abe101 call     0x5809f0                                      
00abe106 mov      byte ptr [rip + 0x56aeda7], r13b              
00abe10d cmp      qword ptr [r15 + 0x438], r12                  
00abe114 je       0xabe257                                      
00abe11a test     rbx, rbx                                      
00abe11d je       0xabe257                                      
00abe123 mov      rcx, qword ptr [r15 + 0x438]                  
00abe12a xor      edx, edx                                      
00abe12c call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00abe131 test     rax, rax                                      
00abe134 je       0xabf595                                      
00abe13a cmp      dword ptr [rax + 0xe0], 7                     
00abe141 jne      0xabe257                                      
00abe147 mov      rdx, qword ptr [rip + 0x52f8d52]              
00abe14e mov      ecx, 2                                        
00abe153 mov      r8, rbx                                       
00abe156 call     0x30d0                                        
00abe15b test     rax, rax                                      
00abe15e je       0xabf595                                      
00abe164 mov      r8, qword ptr [rip + 0x52b9545]               
00abe16b lea      rdx, [rbp + 0xb0]                             
00abe172 mov      rcx, rax                                      
00abe175 call     0xfb2ea0                                      
00abe17a test     al, al                                        
00abe17c je       0xabe257                                      
00abe182 mov      rcx, qword ptr [rbp + 0xb0]                   
00abe189 test     rcx, rcx                                      
00abe18c je       0xabf595                                      
00abe192 xor      edx, edx                                      
00abe194 call     0xc22560                                      
00abe199 mov      dword ptr [r15 + 0x370], eax                  
00abe1a0 mov      rax, qword ptr [rip + 0x52f92a1]              
00abe1a7 cmp      dword ptr [rax + 0xe4], r12d                  
00abe1ae jne      0xabe1bf                                      
00abe1b0 mov      rcx, rax                                      
00abe1b3 call     0x580d30                                      
00abe1b8 mov      rax, qword ptr [rip + 0x52f9289]              
00abe1bf mov      rax, qword ptr [rax + 0xb8]                   
00abe1c6 mov      rax, qword ptr [rax + 0x70]                   
00abe1ca test     rax, rax                                      
00abe1cd je       0xabf595                                      
00abe1d3 mov      rax, qword ptr [rax + 0x50]                   
00abe1d7 test     rax, rax                                      
00abe1da je       0xabf595                                      
00abe1e0 mov      r8, qword ptr [r15 + 0x2f0]                   
00abe1e7 mov      rbx, qword ptr [rax + 0x28]                   
00abe1eb test     r8, r8                                        
00abe1ee je       0xabf595                                      
00abe1f4 mov      rdx, qword ptr [rip + 0x52f8ca5]              
00abe1fb mov      ecx, 2                                        
00abe200 call     0x30d0                                        
00abe205 mov      rcx, qword ptr [rbp + 0xb0]                   
00abe20c mov      rdi, rax                                      
00abe20f test     rcx, rcx                                      
00abe212 je       0xabf595                                      
00abe218 xor      edx, edx                                      
00abe21a call     0x83d120                                      System.String BossGraveStone::get_DisplayName()
00abe21f mov      rdx, qword ptr [rip + 0x5278f7a]              
00abe226 xor      r8d, r8d                                      
00abe229 mov      rcx, rax                                      
00abe22c call     0x2df5370                                     
00abe231 test     rbx, rbx                                      
00abe234 je       0xabf595                                      
00abe23a movss    xmm3, dword ptr [rip + 0x3e538a6]             
00abe242 mov      r8, rax                                       
00abe245 mov      rdx, rdi                                      
00abe248 mov      qword ptr [rsp + 0x20], r12                   
00abe24d mov      rcx, rbx                                      
00abe250 call     0x8bac40                                      UITargetIndicator UITargetIndicator::Draw(UnityEngine.GameObject,System.String,System.Single)
00abe255 jmp      0xabe2c0                                      
00abe257 xor      edx, edx                                      
00abe259 mov      qword ptr [rbp + 0xb0], r12                   
00abe260 lea      rcx, [rbp + 0xb0]                             
00abe267 call     0x57fd40                                      
00abe26c mov      rax, qword ptr [rip + 0x52f91d5]              
00abe273 cmp      dword ptr [rax + 0xe4], r12d                  
00abe27a jne      0xabe28b                                      
00abe27c mov      rcx, rax                                      
00abe27f call     0x580d30                                      
00abe284 mov      rax, qword ptr [rip + 0x52f91bd]              
00abe28b mov      rax, qword ptr [rax + 0xb8]                   
00abe292 mov      rax, qword ptr [rax + 0x70]                   
00abe296 test     rax, rax                                      
00abe299 je       0xabf595                                      
00abe29f mov      rax, qword ptr [rax + 0x50]                   
00abe2a3 test     rax, rax                                      
00abe2a6 je       0xabf595                                      
00abe2ac mov      rcx, qword ptr [rax + 0x28]                   
00abe2b0 test     rcx, rcx                                      
00abe2b3 je       0xabf595                                      
00abe2b9 xor      edx, edx                                      
00abe2bb call     0x8bb370                                      System.Void UITargetIndicator::Hide()
00abe2c0 cmp      byte ptr [r15 + 0x364], r12b                  
00abe2c7 jne      0xabe2e5                                      
00abe2c9 cmp      byte ptr [r15 + 0x365], r12b                  
00abe2d0 je       0xabe7fe                                      
00abe2d6 xor      edx, edx                                      
00abe2d8 mov      rcx, r15                                      
00abe2db call     0xac1050                                      System.Void PlayerController::ClearSkillReady()
00abe2e0 jmp      0xabe7fe                                      
00abe2e5 mov      rax, qword ptr [rip + 0x52f915c]              
00abe2ec cmp      dword ptr [rax + 0xe4], r12d                  
00abe2f3 jne      0xabe304                                      
00abe2f5 mov      rcx, rax                                      
00abe2f8 call     0x580d30                                      
00abe2fd mov      rax, qword ptr [rip + 0x52f9144]              
00abe304 mov      rax, qword ptr [rax + 0xb8]                   
00abe30b mov      rax, qword ptr [rax + 0x70]                   
00abe30f test     rax, rax                                      
00abe312 je       0xabf595                                      
00abe318 mov      rax, qword ptr [rax + 0x50]                   
00abe31c test     rax, rax                                      
00abe31f je       0xabf595                                      
00abe325 mov      rcx, qword ptr [rax + 0x118]                  
00abe32c test     rcx, rcx                                      
00abe32f je       0xabf595                                      
00abe335 xor      edx, edx                                      
00abe337 call     0x88a0a0                                      System.Void UIChat::Unfocus()
00abe33c mov      rax, qword ptr [rip + 0x52f9105]              
00abe343 mov      rcx, qword ptr [rax + 0xb8]                   
00abe34a mov      rcx, qword ptr [rcx + 0x70]                   
00abe34e test     rcx, rcx                                      
00abe351 je       0xabf595                                      
00abe357 mov      rcx, qword ptr [rcx + 0x50]                   
00abe35b test     rcx, rcx                                      
00abe35e je       0xabf595                                      
00abe364 xor      edx, edx                                      
00abe366 call     0x894960                                      System.Void UIGame::CloseContextMenu()
00abe36b cmp      dword ptr [r15 + 0x36c], r12d                 
00abe372 jle      0xabe433                                      
00abe378 mov      rcx, qword ptr [rip + 0x529dcc1]              
00abe37f mov      rbx, qword ptr [r15 + 0x2e0]                  
00abe386 cmp      dword ptr [rcx + 0xe4], r12d                  
00abe38d jne      0xabe394                                      
00abe38f call     0x580d30                                      
00abe394 xor      edx, edx                                      
00abe396 mov      rcx, rbx                                      
00abe399 call     0x443daf0                                     
00abe39e test     al, al                                        
00abe3a0 je       0xabe3cd                                      
00abe3a2 mov      rcx, qword ptr [r15 + 0x2e0]                  
00abe3a9 mov      ebx, dword ptr [r15 + 0x36c]                  
00abe3b0 test     rcx, rcx                                      
00abe3b3 je       0xabf595                                      
00abe3b9 xor      edx, edx                                      
00abe3bb call     0xc22560                                      
00abe3c0 cmp      ebx, eax                                      
00abe3c2 jne      0xabe3cd                                      
00abe3c4 mov      rdx, qword ptr [r15 + 0x2e0]                  
00abe3cb jmp      0xabe420                                      
00abe3cd mov      rcx, qword ptr [rip + 0x529dc6c]              
00abe3d4 mov      rbx, qword ptr [r15 + 0x2e8]                  
00abe3db cmp      dword ptr [rcx + 0xe4], r12d                  
00abe3e2 jne      0xabe3e9                                      
00abe3e4 call     0x580d30                                      
00abe3e9 xor      edx, edx                                      
00abe3eb mov      rcx, rbx                                      
00abe3ee call     0x443daf0                                     
00abe3f3 test     al, al                                        
00abe3f5 je       0xabe433                                      
00abe3f7 mov      rcx, qword ptr [r15 + 0x2e8]                  
00abe3fe mov      ebx, dword ptr [r15 + 0x36c]                  
00abe405 test     rcx, rcx                                      
00abe408 je       0xabf595                                      
00abe40e xor      edx, edx                                      
00abe410 call     0xc22560                                      
00abe415 cmp      ebx, eax                                      
00abe417 jne      0xabe433                                      
00abe419 mov      rdx, qword ptr [r15 + 0x2e8]                  
00abe420 mov      r8, r12                                       
00abe423 mov      rcx, r15                                      
00abe426 call     0xad2a30                                      System.Boolean PlayerController::ProcessClickedUnit(BaseUnitController)
00abe42b test     al, al                                        
00abe42d jne      0xabe7fe                                      
00abe433 mov      rbx, qword ptr [r15 + 0x2f0]                  
00abe43a cmp      qword ptr [r15 + 0x438], r12                  
00abe441 jne      0xabe6a7                                      
00abe447 test     rbx, rbx                                      
00abe44a jne      0xabe586                                      
00abe450 movsd    xmm1, qword ptr [r15 + 0x2d0]                 
00abe459 xor      eax, eax                                      
00abe45b movaps   xmm2, xmm1                                    
00abe45e movsd    qword ptr [rsp + 0x50], xmm1                  
00abe464 movaps   xmm3, xmm1                                    
00abe467 mov      qword ptr [rsp + 0x40], rax                   
00abe46c movss    xmm1, dword ptr [r15 + 0x2d8]                 
00abe475 movd     xmm0, eax                                     
00abe479 subss    xmm2, xmm0                                    
00abe47d shufps   xmm3, xmm3, 0x55                              
00abe481 subss    xmm3, dword ptr [rsp + 0x44]                  
00abe487 movd     xmm0, eax                                     
00abe48b subss    xmm1, xmm0                                    
00abe48f movss    xmm0, dword ptr [rip + 0x3e5285d]             
00abe497 mulss    xmm3, xmm3                                    
00abe49b mulss    xmm2, xmm2                                    
00abe49f mulss    xmm1, xmm1                                    
00abe4a3 addss    xmm3, xmm2                                    
00abe4a7 addss    xmm3, xmm1                                    
00abe4ab comiss   xmm0, xmm3                                    
00abe4ae ja       0xabe7fe                                      
00abe4b4 test     r14b, r14b                                    
00abe4b7 jne      0xabe7fe                                      
00abe4bd xor      edx, edx                                      
00abe4bf lea      ecx, [rbx + 0x31]                             
00abe4c2 call     0xaa9250                                      System.Boolean HotkeyManager::GetKey(Hotkey)
00abe4c7 test     al, al                                        
00abe4c9 jne      0xabe7fe                                      
00abe4cf mov      rax, qword ptr [rip + 0x52f07c2]              
00abe4d6 cmp      dword ptr [rax + 0xe4], r12d                  
00abe4dd jne      0xabe4ee                                      
00abe4df mov      rcx, rax                                      
00abe4e2 call     0x580d30                                      
00abe4e7 mov      rax, qword ptr [rip + 0x52f07aa]              
00abe4ee mov      rax, qword ptr [rax + 0xb8]                   
00abe4f5 mov      rcx, qword ptr [rax + 0x98]                   
00abe4fc test     rcx, rcx                                      
00abe4ff je       0xabf595                                      
00abe505 cmp      byte ptr [rcx + 0x10], r12b                   
00abe509 je       0xabe7fe                                      
00abe50f mov      rax, qword ptr [r15 + 0x1f8]                  
00abe516 test     rax, rax                                      
00abe519 je       0xabf595                                      
00abe51f cmp      byte ptr [rax + 0x5f], r12b                   
00abe523 jne      0xabe7fe                                      
00abe529 mov      rcx, qword ptr [rip + 0x52bbe68]              
00abe530 movsd    xmm6, qword ptr [r15 + 0x2d0]                 
00abe539 mov      ebx, dword ptr [r15 + 0x2d8]                  
00abe540 cmp      dword ptr [rcx + 0xe4], r12d                  
00abe547 jne      0xabe54e                                      
00abe549 call     0x580d30                                      
00abe54e xor      r8d, r8d                                      
00abe551 movsd    qword ptr [rsp + 0x30], xmm6                  
00abe557 lea      rdx, [rsp + 0x30]                             
00abe55c mov      dword ptr [rsp + 0x38], ebx                   
00abe560 lea      rcx, [rsp + 0x50]                             
00abe565 call     0x7f8040                                      UnityEngine.Vector3Int Extensions::CompressV3(UnityEngine.Vector3)
00abe56a movsd    xmm0, qword ptr [rax]                         
00abe56e mov      ecx, dword ptr [rax + 8]                      
00abe571 movsd    qword ptr [r15 + 0x334], xmm0                 
00abe57a mov      dword ptr [r15 + 0x33c], ecx                  
00abe581 jmp      0xabe7d4                                      
00abe586 mov      rdx, qword ptr [rip + 0x52f8a43]              
00abe58d mov      rcx, qword ptr [r15 + 0x2f0]                  
00abe594 call     0x57fd60                                      
00abe599 mov      rbx, rax                                      
00abe59c test     rax, rax                                      
00abe59f jne      0xabe611                                      
00abe5a1 mov      r8, qword ptr [r15 + 0x2f0]                   
00abe5a8 test     r8, r8                                        
00abe5ab je       0xabf595                                      
00abe5b1 mov      rdx, qword ptr [rip + 0x52f88e8]              
00abe5b8 lea      ecx, [rax + 2]                                
00abe5bb call     0x30d0                                        
00abe5c0 test     rax, rax                                      
00abe5c3 je       0xabf595                                      
00abe5c9 xor      edx, edx                                      
00abe5cb mov      rcx, rax                                      
00abe5ce call     0x443d9e0                                     
00abe5d3 lea      rcx, [r15 + 0x378]                            
00abe5da mov      qword ptr [r15 + 0x378], rax                  
00abe5e1 mov      rdx, rax                                      
00abe5e4 call     0x57fd40                                      
00abe5e9 mov      r8, qword ptr [r15 + 0x2f0]                   
00abe5f0 test     r8, r8                                        
00abe5f3 je       0xabf595                                      
00abe5f9 mov      rdx, qword ptr [rip + 0x52f88a0]              
00abe600 lea      ecx, [rbx + 4]                                
00abe603 call     0x30d0                                        
00abe608 mov      byte ptr [r15 + 0x380], al                    
00abe60f jmp      0xabe676                                      
00abe611 mov      r10, qword ptr [rax]                          
00abe614 movzx    ecx, r12w                                     
00abe618 mov      r9, qword ptr [rip + 0x52f89b1]               
00abe61f movzx    edx, word ptr [r10 + 0x12e]                   
00abe627 cmp      r12w, dx                                      
00abe62b jae      0xabe648                                      
00abe62d mov      r8, qword ptr [r10 + 0xb0]                    
00abe634 movzx    eax, cx                                       
00abe637 add      rax, rax                                      
00abe63a cmp      qword ptr [r8 + rax*8], r9                    
00abe63e je       0xabe68d                                      
00abe640 inc      cx                                            
00abe643 cmp      cx, dx                                        
00abe646 jb       0xabe634                                      
00abe648 xor      r8d, r8d                                      
00abe64b mov      rdx, r9                                       
00abe64e mov      rcx, rbx                                      
00abe651 call     0x57dd50                                      
00abe656 mov      r8, qword ptr [rax]                           
00abe659 mov      rcx, rbx                                      
00abe65c mov      rdx, qword ptr [rax + 8]                      
00abe660 call     r8                                            
00abe663 test     rax, rax                                      
00abe666 je       0xabf595                                      
00abe66c mov      eax, dword ptr [rax + 0x44]                   
00abe66f mov      dword ptr [r15 + 0x370], eax                  
00abe676 mov      rdx, qword ptr [r15 + 0x2f0]                  
00abe67d xor      r8d, r8d                                      
00abe680 mov      rcx, r15                                      
00abe683 call     0xad2450                                      System.Void PlayerController::ProcessClickedInteractable(IInteractable)
00abe688 jmp      0xabe7fe                                      
00abe68d movzx    ecx, cx                                       
00abe690 add      rcx, rcx                                      
00abe693 movsxd   rax, dword ptr [r8 + rcx*8 + 8]               
00abe698 shl      rax, 4                                        
00abe69c add      rax, 0x138                                    
00abe6a2 add      rax, r10                                      
00abe6a5 jmp      0xabe656                                      
00abe6a7 cmp      byte ptr [rip + 0x56ae806], r12b              
00abe6ae jne      0xabe6cf                                      
00abe6b0 lea      rcx, [rip + 0x52b8ff9]                        
00abe6b7 call     0x5809f0                                      
00abe6bc lea      rcx, [rip + 0x52f87dd]                        
00abe6c3 call     0x5809f0                                      
00abe6c8 mov      byte ptr [rip + 0x56ae7e5], r13b              
00abe6cf cmp      qword ptr [r15 + 0x438], r12                  
00abe6d6 je       0xabe74d                                      
00abe6d8 test     rbx, rbx                                      
00abe6db je       0xabe74d                                      
00abe6dd mov      rcx, qword ptr [r15 + 0x438]                  
00abe6e4 xor      edx, edx                                      
00abe6e6 call     0x7d5fe0                                      SkillConfig SkillState::get_Config()
00abe6eb test     rax, rax                                      
00abe6ee je       0xabf595                                      
00abe6f4 cmp      dword ptr [rax + 0xe0], 7                     
00abe6fb jne      0xabe74d                                      
00abe6fd mov      rdx, qword ptr [rip + 0x52f879c]              
00abe704 mov      ecx, 2                                        
00abe709 mov      r8, rbx                                       
00abe70c call     0x30d0                                        
00abe711 test     rax, rax                                      
00abe714 je       0xabf595                                      
00abe71a mov      r8, qword ptr [rip + 0x52b8f8f]               
00abe721 lea      rdx, [rbp + 0xb8]                             
00abe728 mov      rcx, rax                                      
00abe72b call     0xfb2ea0                                      
00abe730 test     al, al                                        
00abe732 je       0xabe74d                                      
00abe734 mov      rax, qword ptr [rbp + 0xb8]                   
00abe73b test     rax, rax                                      
00abe73e je       0xabf595                                      
00abe744 mov      rax, qword ptr [rax + 0x30]                   
00abe748 jmp      0xabe663                                      
00abe74d xor      edx, edx                                      
00abe74f mov      qword ptr [rbp + 0xb8], r12                   
00abe756 lea      rcx, [rbp + 0xb8]                             
00abe75d call     0x57fd40                                      
00abe762 mov      rax, qword ptr [r15 + 0x1f8]                  
00abe769 test     rax, rax                                      
00abe76c je       0xabf595                                      
00abe772 cmp      byte ptr [rax + 0x5f], r12b                   
00abe776 jne      0xabe7fe                                      
00abe77c mov      rcx, qword ptr [rip + 0x52bbc15]              
00abe783 movsd    xmm6, qword ptr [r15 + 0x2d0]                 
00abe78c mov      ebx, dword ptr [r15 + 0x2d8]                  
00abe793 cmp      dword ptr [rcx + 0xe4], r12d                  
00abe79a jne      0xabe7a1                                      
00abe79c call     0x580d30                                      
00abe7a1 xor      r8d, r8d                                      
00abe7a4 movsd    qword ptr [rsp + 0x30], xmm6                  
00abe7aa lea      rdx, [rsp + 0x30]                             
00abe7af mov      dword ptr [rsp + 0x38], ebx                   
00abe7b3 lea      rcx, [rsp + 0x50]                             
00abe7b8 call     0x7f8040                                      UnityEngine.Vector3Int Extensions::CompressV3(UnityEngine.Vector3)
00abe7bd movsd    xmm0, qword ptr [rax]                         
00abe7c1 mov      edx, dword ptr [rax + 8]                      
00abe7c4 movsd    qword ptr [r15 + 0x334], xmm0                 
00abe7cd mov      dword ptr [r15 + 0x33c], edx                  
00abe7d4 movsd    xmm0, qword ptr [r15 + 0x2d0]                 
00abe7dd lea      rdx, [rsp + 0x30]                             
00abe7e2 mov      eax, dword ptr [r15 + 0x2d8]                  
00abe7e9 xor      r8d, r8d                                      
00abe7ec mov      rcx, r15                                      
00abe7ef movsd    qword ptr [rsp + 0x30], xmm0                  
00abe7f5 mov      dword ptr [rsp + 0x38], eax                   
00abe7f9 call     0xad24f0                                      System.Void PlayerController::ProcessClickedPosition(UnityEngine.Vector3)
00abe7fe xor      edx, edx                                      
00abe800 lea      ecx, [rdx + 0x31]                             
00abe803 call     0xaa9250                                      System.Boolean HotkeyManager::GetKey(Hotkey)
00abe808 test     al, al                                        
00abe80a jne      0xabe985                                      
00abe810 xor      edx, edx                                      
00abe812 mov      ecx, 0x143                                    
00abe817 call     0x44d2110                                     
00abe81c test     al, al                                        
00abe81e je       0xabe830                                      
00abe820 xor      ecx, ecx                                      
00abe822 call     0x444af50                                     
00abe827 movss    dword ptr [r15 + 0x318], xmm0                 
00abe830 xor      ecx, ecx                                      
00abe832 call     0x444af50                                     
00abe837 movss    xmm7, dword ptr [r15 + 0x318]                 
00abe840 xor      edx, edx                                      
00abe842 mov      ecx, 0x143                                    
00abe847 movaps   xmm6, xmm0                                    
00abe84a call     0x44d2150                                     
00abe84f test     al, al                                        
00abe851 je       0xabe96a                                      
00abe857 subss    xmm6, xmm7                                    
00abe85b comiss   xmm6, dword ptr [rip + 0x3e524ba]             
00abe862 jb       0xabe96a                                      
00abe868 mov      rax, qword ptr [rip + 0x52f0429]              
00abe86f cmp      dword ptr [rax + 0xe4], r12d                  
00abe876 jne      0xabe887                                      
00abe878 mov      rcx, rax                                      
00abe87b call     0x580d30                                      
00abe880 mov      rax, qword ptr [rip + 0x52f0411]              
00abe887 mov      rax, qword ptr [rax + 0xb8]                   
00abe88e mov      rcx, qword ptr [rax + 0x98]                   
00abe895 test     rcx, rcx                                      
00abe898 je       0xabf595                                      
00abe89e cmp      byte ptr [rcx + 0x10], r12b                   
00abe8a2 je       0xabe96a                                      
00abe8a8 movsd    xmm6, qword ptr [r15 + 0x2d0]                 
00abe8b1 lea      rcx, [rsp + 0x50]                             
00abe8b6 mov      ebx, dword ptr [r15 + 0x2d8]                  
00abe8bd xor      r8d, r8d                                      
00abe8c0 mov      rdx, r15                                      
00abe8c3 call     0x6f00c0                                      UnityEngine.Vector3 BaseUnitController::get_Position()
00abe8c8 movaps   xmm3, xmm6                                    
00abe8cb movsd    qword ptr [rsp + 0x30], xmm6                  
00abe8d1 movaps   xmm2, xmm6                                    
00abe8d4 shufps   xmm2, xmm2, 0x55                              
00abe8d8 movsd    xmm1, qword ptr [rax]                         
00abe8dc movaps   xmm0, xmm1                                    
00abe8df movsd    qword ptr [rsp + 0x30], xmm1                  
00abe8e5 subss    xmm3, xmm1                                    
00abe8e9 shufps   xmm0, xmm0, 0x55                              
00abe8ed movd     xmm1, ebx                                     
00abe8f1 subss    xmm2, xmm0                                    
00abe8f5 subss    xmm1, dword ptr [rax + 8]                     
00abe8fa unpcklps xmm3, xmm2                                    
00abe8fd lea      rdx, [rsp + 0x40]                             
00abe902 xor      r8d, r8d                                      
00abe905 movsd    qword ptr [rsp + 0x40], xmm3                  
00abe90b lea      rcx, [rsp + 0x50]                             
00abe910 movss    dword ptr [rsp + 0x48], xmm1                  
00abe916 call     0x6c76b0                                      
00abe91b mov      rcx, qword ptr [rip + 0x52bba76]              
00abe922 movsd    xmm6, qword ptr [rax]                         
00abe926 mov      ebx, dword ptr [rax + 8]                      
00abe929 cmp      dword ptr [rcx + 0xe4], r12d                  
00abe930 jne      0xabe937                                      
00abe932 call     0x580d30                                      
00abe937 xor      r8d, r8d                                      
00abe93a movsd    qword ptr [rsp + 0x30], xmm6                  
00abe940 lea      rdx, [rsp + 0x30]                             
00abe945 mov      dword ptr [rsp + 0x38], ebx                   
00abe949 lea      rcx, [rsp + 0x50]                             
00abe94e call     0x7f8040                                      UnityEngine.Vector3Int Extensions::CompressV3(UnityEngine.Vector3)
00abe953 movsd    xmm0, qword ptr [rax]                         
00abe957 mov      edx, dword ptr [rax + 8]                      
00abe95a movsd    qword ptr [r15 + 0x328], xmm0                 
00abe963 mov      dword ptr [r15 + 0x330], edx                  
00abe96a xor      edx, edx                                      
00abe96c mov      ecx, 0x143                                    
00abe971 call     0x44d2190                                     
00abe976 test     al, al                                        
00abe978 je       0xabe985                                      
00abe97a mov      dword ptr [r15 + 0x318], 0xbf800000           
00abe985 xor      r8d, r8d                                      
00abe988 lea      rcx, [r15 + 0x328]                            
00abe98f lea      edx, [r8 + 0x38]                              
00abe993 call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abe998 test     al, al                                        
00abe99a je       0xabe9d6                                      
00abe99c mov      rax, qword ptr [rip + 0x52f8aa5]              
00abe9a3 cmp      dword ptr [rax + 0xe4], r12d                  
00abe9aa jne      0xabe9bb                                      
00abe9ac mov      rcx, rax                                      
00abe9af call     0x580d30                                      
00abe9b4 mov      rax, qword ptr [rip + 0x52f8a8d]              
00abe9bb mov      rax, qword ptr [rax + 0xb8]                   
00abe9c2 mov      rcx, qword ptr [rax + 0x70]                   
00abe9c6 test     rcx, rcx                                      
00abe9c9 je       0xabf595                                      
00abe9cf xor      edx, edx                                      
00abe9d1 call     0x920fb0                                      System.Void UIManager::ToggleDisplayed()
00abe9d6 xor      r8d, r8d                                      
00abe9d9 lea      rcx, [r15 + 0x328]                            
00abe9e0 lea      edx, [r8 + 0x2d]                              
00abe9e4 call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abe9e9 test     al, al                                        
00abe9eb je       0xabeb4e                                      
00abe9f1 mov      eax, dword ptr [r15 + 0x32c]                  
00abe9f8 mov      ecx, dword ptr [r15 + 0x328]                  
00abe9ff mov      edx, dword ptr [r15 + 0x330]                  
00abea06 imul     ecx, ecx                                      
00abea09 imul     eax, eax                                      
00abea0c imul     edx, edx                                      
00abea0f add      ecx, eax                                      
00abea11 add      ecx, edx                                      
00abea13 test     ecx, ecx                                      
00abea15 jle      0xabea54                                      
00abea17 movsd    xmm0, qword ptr [r15 + 0x328]                 
00abea20 movsd    qword ptr [rsp + 0x30], xmm0                  
00abea26 mov      rax, qword ptr [rsp + 0x30]                   
00abea2b movd     xmm0, dword ptr [rsp + 0x30]                  
00abea31 movd     xmm2, dword ptr [r15 + 0x330]                 
00abea3a shr      rax, 0x20                                     
00abea3e cvtdq2ps xmm6, xmm0                                    
00abea41 movd     xmm1, eax                                     
00abea45 cvtdq2ps xmm1, xmm1                                    
00abea48 cvtdq2ps xmm2, xmm2                                    
00abea4b unpcklps xmm6, xmm1                                    
00abea4e movd     ebx, xmm2                                     
00abea52 jmp      0xabea7c                                      
00abea54 mov      rax, qword ptr [r15 + 0x120]                  
00abea5b test     rax, rax                                      
00abea5e je       0xabf595                                      
00abea64 mov      rax, qword ptr [rax + 0x118]                  
00abea6b test     rax, rax                                      
00abea6e je       0xabf595                                      
00abea74 movsd    xmm6, qword ptr [rax + 0x28]                  
00abea79 mov      ebx, dword ptr [rax + 0x30]                   
00abea7c xor      r8d, r8d                                      
00abea7f lea      rcx, [rsp + 0x50]                             
00abea84 mov      rdx, r15                                      
00abea87 call     0x6f00c0                                      UnityEngine.Vector3 BaseUnitController::get_Position()
00abea8c mov      rcx, qword ptr [rip + 0x52bb905]              
00abea93 movsd    xmm7, qword ptr [rax]                         
00abea97 mov      edi, dword ptr [rax + 8]                      
00abea9a cmp      dword ptr [rcx + 0xe4], r12d                  
00abeaa1 jne      0xabeaa8                                      
00abeaa3 call     0x580d30                                      
00abeaa8 xor      r8d, r8d                                      
00abeaab movsd    qword ptr [rsp + 0x30], xmm7                  
00abeab1 lea      rdx, [rsp + 0x30]                             
00abeab6 mov      dword ptr [rsp + 0x38], edi                   
00abeaba lea      rcx, [rsp + 0x50]                             
00abeabf call     0x7f8040                                      UnityEngine.Vector3Int Extensions::CompressV3(UnityEngine.Vector3)
00abeac4 xor      r8d, r8d                                      
00abeac7 movsd    qword ptr [rsp + 0x30], xmm6                  
00abeacd lea      rdx, [rsp + 0x30]                             
00abead2 mov      dword ptr [rsp + 0x38], ebx                   
00abead6 mov      ecx, dword ptr [rax + 8]                      
00abead9 movsd    xmm0, qword ptr [rax]                         
00abeadd movsd    qword ptr [r15 + 0x34c], xmm0                 
00abeae6 mov      dword ptr [r15 + 0x354], ecx                  
00abeaed lea      rcx, [rsp + 0x50]                             
00abeaf2 call     0x7f8040                                      UnityEngine.Vector3Int Extensions::CompressV3(UnityEngine.Vector3)
00abeaf7 xor      r8d, r8d                                      
00abeafa movsd    qword ptr [rsp + 0x30], xmm6                  
00abeb00 mov      rdx, r15                                      
00abeb03 mov      dword ptr [rsp + 0x38], ebx                   
00abeb07 mov      ecx, dword ptr [rax + 8]                      
00abeb0a movsd    xmm0, qword ptr [rax]                         
00abeb0e movsd    qword ptr [r15 + 0x358], xmm0                 
00abeb17 mov      dword ptr [r15 + 0x360], ecx                  
00abeb1e lea      rcx, [rsp + 0x50]                             
00abeb23 call     0x6f00c0                                      UnityEngine.Vector3 BaseUnitController::get_Position()
00abeb28 xor      r9d, r9d                                      
00abeb2b lea      r8, [rsp + 0x30]                              
00abeb30 lea      rdx, [rsp + 0x40]                             
00abeb35 mov      rcx, r15                                      
00abeb38 movsd    xmm0, qword ptr [rax]                         
00abeb3c mov      eax, dword ptr [rax + 8]                      
00abeb3f movsd    qword ptr [rsp + 0x40], xmm0                  
00abeb45 mov      dword ptr [rsp + 0x48], eax                   
00abeb49 call     0x6e6470                                      System.Void BaseUnitController::DodgeRoll(UnityEngine.Vector3,UnityEngine.Vector3)
00abeb4e xor      r8d, r8d                                      
00abeb51 lea      rcx, [r15 + 0x328]                            
00abeb58 lea      edx, [r8 + 0x2e]                              
00abeb5c call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abeb61 test     al, al                                        
00abeb63 je       0xabebac                                      
00abeb65 lea      rcx, [r15 + 0x410]                            
00abeb6c mov      qword ptr [r15 + 0x410], r12                  
00abeb73 xor      edx, edx                                      
00abeb75 call     0x57fd40                                      
00abeb7a lea      rcx, [r15 + 0x440]                            
00abeb81 mov      qword ptr [r15 + 0x440], r12                  
00abeb88 xor      edx, edx                                      
00abeb8a call     0x57fd40                                      
00abeb8f mov      rcx, qword ptr [r15 + 0x130]                  
00abeb96 test     rcx, rcx                                      
00abeb99 je       0xabf595                                      
00abeb9f xor      r9d, r9d                                      
00abeba2 xor      r8d, r8d                                      
00abeba5 xor      edx, edx                                      
00abeba7 call     0x84c9f0                                      System.Void CombatComponent::SetTarget(BaseUnitController,System.Boolean)
00abebac xor      r8d, r8d                                      
00abebaf lea      rcx, [r15 + 0x328]                            
00abebb6 lea      edx, [r8 + 0x39]                              
00abebba call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abebbf test     al, al                                        
00abebc1 je       0xabec0a                                      
00abebc3 lea      rcx, [r15 + 0x410]                            
00abebca mov      qword ptr [r15 + 0x410], r12                  
00abebd1 xor      edx, edx                                      
00abebd3 call     0x57fd40                                      
00abebd8 lea      rcx, [r15 + 0x440]                            
00abebdf mov      qword ptr [r15 + 0x440], r12                  
00abebe6 xor      edx, edx                                      
00abebe8 call     0x57fd40                                      
00abebed mov      rcx, qword ptr [r15 + 0x130]                  
00abebf4 test     rcx, rcx                                      
00abebf7 je       0xabf595                                      
00abebfd xor      r9d, r9d                                      
00abec00 xor      r8d, r8d                                      
00abec03 xor      edx, edx                                      
00abec05 call     0x84c9f0                                      System.Void CombatComponent::SetTarget(BaseUnitController,System.Boolean)
00abec0a mov      rax, qword ptr [rip + 0x52f8837]              
00abec11 cmp      dword ptr [rax + 0xe4], r12d                  
00abec18 jne      0xabec29                                      
00abec1a mov      rcx, rax                                      
00abec1d call     0x580d30                                      
00abec22 mov      rax, qword ptr [rip + 0x52f881f]              
00abec29 mov      rax, qword ptr [rax + 0xb8]                   
00abec30 mov      rax, qword ptr [rax + 0x70]                   
00abec34 test     rax, rax                                      
00abec37 je       0xabf595                                      
00abec3d mov      rax, qword ptr [rax + 0x50]                   
00abec41 test     rax, rax                                      
00abec44 je       0xabf595                                      
00abec4a mov      rcx, qword ptr [rax + 0x38]                   
00abec4e test     rcx, rcx                                      
00abec51 je       0xabf595                                      
00abec57 xor      r9d, r9d                                      
00abec5a xor      r8d, r8d                                      
00abec5d xor      edx, edx                                      
00abec5f call     0x87b940                                      System.Void UIActionPrompt::Draw(System.String,System.String)
00abec64 cmp      qword ptr [r15 + 0x438], r12                  
00abec6b jne      0xabf27c                                      
00abec71 mov      rax, qword ptr [rip + 0x52f87d0]              
00abec78 cmp      dword ptr [rax + 0xe4], r12d                  
00abec7f jne      0xabec90                                      
00abec81 mov      rcx, rax                                      
00abec84 call     0x580d30                                      
00abec89 mov      rax, qword ptr [rip + 0x52f87b8]              
00abec90 mov      rax, qword ptr [rax + 0xb8]                   
00abec97 mov      rdx, qword ptr [rax]                          
00abec9a test     rdx, rdx                                      
00abec9d je       0xabf595                                      
00abeca3 mov      rax, qword ptr [rip + 0x52d512e]              
00abecaa lea      r9, [rsp + 0x70]                              
00abecaf movss    xmm2, dword ptr [rip + 0x3e51fc9]             
00abecb7 mov      rcx, r15                                      
00abecba mov      edx, dword ptr [rdx + 0x164]                  
00abecc0 mov      qword ptr [rsp + 0x28], rax                   
00abecc5 mov      qword ptr [rsp + 0x20], r12                   
00abecca call     0x10ab570                                     System.Boolean PlayerController::FindNearby(UnityEngine.LayerMask,System.Single,T&,Il2CppSystem.Func`2<T,System.Boolean>)
00abeccf test     al, al                                        
00abecd1 je       0xabed3f                                      
00abecd3 mov      rax, qword ptr [rip + 0x52f876e]              
00abecda cmp      dword ptr [rax + 0xe4], r12d                  
00abece1 jne      0xabecf2                                      
00abece3 mov      rcx, rax                                      
00abece6 call     0x580d30                                      
00abeceb mov      rax, qword ptr [rip + 0x52f8756]              
00abecf2 mov      rax, qword ptr [rax + 0xb8]                   
00abecf9 mov      rcx, qword ptr [rax + 0x70]                   
00abecfd test     rcx, rcx                                      
00abed00 je       0xabf595                                      
00abed06 mov      rax, qword ptr [rcx + 0x50]                   
00abed0a test     rax, rax                                      
00abed0d je       0xabf595                                      
00abed13 mov      rbx, qword ptr [rax + 0x38]                   
00abed17 xor      edx, edx                                      
00abed19 lea      ecx, [rdx + 0x2f]                             
00abed1c call     0xaa8c70                                      System.String HotkeyManager::GetKeyDisplayName(Hotkey)
00abed21 test     rbx, rbx                                      
00abed24 je       0xabf595                                      
00abed2a mov      rdx, qword ptr [rip + 0x533b6d7]              
00abed31 xor      r9d, r9d                                      
00abed34 mov      r8, rax                                       
00abed37 mov      rcx, rbx                                      
00abed3a call     0x87b940                                      System.Void UIActionPrompt::Draw(System.String,System.String)
00abed3f xor      r8d, r8d                                      
00abed42 lea      rcx, [r15 + 0x328]                            
00abed49 lea      edx, [r8 + 0x2c]                              
00abed4d call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abed52 xor      edx, edx                                      
00abed54 movzx    edi, al                                       
00abed57 lea      ecx, [rdx + 0x2c]                             
00abed5a call     0xaa8c70                                      System.String HotkeyManager::GetKeyDisplayName(Hotkey)
00abed5f mov      rcx, qword ptr [rip + 0x529d2da]              
00abed66 mov      rsi, rax                                      
00abed69 mov      rbx, qword ptr [r15 + 0x2e8]                  
00abed70 cmp      dword ptr [rcx + 0xe4], r12d                  
00abed77 jne      0xabed7e                                      
00abed79 call     0x580d30                                      
00abed7e xor      edx, edx                                      
00abed80 mov      rcx, rbx                                      
00abed83 call     0x443daf0                                     
00abed88 test     al, al                                        
00abed8a je       0xabef01                                      
00abed90 mov      rcx, qword ptr [rip + 0x529d2a9]              
00abed97 mov      rbx, qword ptr [r15 + 0x2e8]                  
00abed9e cmp      dword ptr [rcx + 0xe4], r12d                  
00abeda5 jne      0xabedac                                      
00abeda7 call     0x580d30                                      
00abedac xor      r8d, r8d                                      
00abedaf mov      rdx, r15                                      
00abedb2 mov      rcx, rbx                                      
00abedb5 call     0x443db80                                     
00abedba test     al, al                                        
00abedbc je       0xabef01                                      
00abedc2 mov      rbx, qword ptr [r15 + 0x2e8]                  
00abedc9 test     rbx, rbx                                      
00abedcc je       0xabef01                                      
00abedd2 mov      rdx, qword ptr [rip + 0x52ada7f]              
00abedd9 mov      r8, qword ptr [rbx]                           
00abeddc movzx    eax, byte ptr [rdx + 0x130]                   
00abede3 cmp      byte ptr [r8 + 0x130], al                     
00abedea jb       0xabef01                                      
00abedf0 movzx    ecx, al                                       
00abedf3 mov      rax, qword ptr [r8 + 0xc8]                    
00abedfa cmp      qword ptr [rax + rcx*8 - 8], rdx              
00abedff jne      0xabef01                                      
00abee05 mov      rcx, qword ptr [rbx + 0x148]                  
00abee0c mov      rax, rbx                                      
00abee0f test     rcx, rcx                                      
00abee12 je       0xabf595                                      
00abee18 xor      edx, edx                                      
00abee1a call     0x819f50                                      BaseUnitController SummoningComponent::get_Summoner()
00abee1f mov      rcx, qword ptr [rip + 0x529d21a]              
00abee26 mov      r14, rax                                      
00abee29 cmp      dword ptr [rcx + 0xe4], r12d                  
00abee30 jne      0xabee37                                      
00abee32 call     0x580d30                                      
00abee37 xor      edx, edx                                      
00abee39 mov      rcx, r14                                      
00abee3c call     0x443daf0                                     
00abee41 test     al, al                                        
00abee43 jne      0xabef01                                      
00abee49 mov      rax, qword ptr [rip + 0x52f85f8]              
00abee50 cmp      dword ptr [rax + 0xe4], r12d                  
00abee57 jne      0xabee68                                      
00abee59 mov      rcx, rax                                      
00abee5c call     0x580d30                                      
00abee61 mov      rax, qword ptr [rip + 0x52f85e0]              
00abee68 mov      rax, qword ptr [rax + 0xb8]                   
00abee6f mov      rax, qword ptr [rax + 0x70]                   
00abee73 test     rax, rax                                      
00abee76 je       0xabf595                                      
00abee7c mov      rax, qword ptr [rax + 0x50]                   
00abee80 test     rax, rax                                      
00abee83 je       0xabf595                                      
00abee89 mov      rcx, qword ptr [rax + 0x38]                   
00abee8d test     rcx, rcx                                      
00abee90 je       0xabf595                                      
00abee96 mov      rdx, qword ptr [rip + 0x52f87f3]              
00abee9d xor      r9d, r9d                                      
00abeea0 mov      r8, rsi                                       
00abeea3 call     0x87b940                                      System.Void UIActionPrompt::Draw(System.String,System.String)
00abeea8 test     dil, dil                                      
00abeeab je       0xabf27c                                      
00abeeb1 mov      rax, qword ptr [rip + 0x52f8590]              
00abeeb8 cmp      dword ptr [rax + 0xe4], r12d                  
00abeebf jne      0xabeed0                                      
00abeec1 mov      rcx, rax                                      
00abeec4 call     0x580d30                                      
00abeec9 mov      rax, qword ptr [rip + 0x52f8578]              
00abeed0 mov      rax, qword ptr [rax + 0xb8]                   
00abeed7 mov      rcx, qword ptr [rax + 0x70]                   
00abeedb test     rcx, rcx                                      
00abeede je       0xabf595                                      
00abeee4 mov      rcx, qword ptr [rcx + 0x50]                   
00abeee8 test     rcx, rcx                                      
00abeeeb je       0xabf595                                      
00abeef1 xor      r8d, r8d                                      
00abeef4 mov      rdx, rbx                                      
00abeef7 call     0x894a70                                      System.Void UIGame::DrawContextMenu(PlayerController)
00abeefc jmp      0xabf27c                                      
00abef01 mov      rcx, qword ptr [rip + 0x529d138]              
00abef08 mov      rbx, qword ptr [r15 + 0x2e0]                  
00abef0f cmp      dword ptr [rcx + 0xe4], r12d                  
00abef16 jne      0xabef1d                                      
00abef18 call     0x580d30                                      
00abef1d xor      edx, edx                                      
00abef1f mov      rcx, rbx                                      
00abef22 call     0x443daf0                                     
00abef27 test     al, al                                        
00abef29 je       0xabf0b7                                      
00abef2f mov      rax, qword ptr [r15 + 0x2e0]                  
00abef36 test     rax, rax                                      
00abef39 je       0xabf0b7                                      
00abef3f mov      r8, qword ptr [rax]                           
00abef42 mov      rdx, qword ptr [rip + 0x5285ef7]              
00abef49 movzx    eax, byte ptr [rdx + 0x130]                   
00abef50 cmp      byte ptr [r8 + 0x130], al                     
00abef57 jb       0xabf0b7                                      
00abef5d movzx    ecx, al                                       
00abef60 mov      rax, qword ptr [r8 + 0xc8]                    
00abef67 cmp      qword ptr [rax + rcx*8 - 8], rdx              
00abef6c jne      0xabf0b7                                      
00abef72 mov      rax, qword ptr [rip + 0x52f84cf]              
00abef79 cmp      dword ptr [rax + 0xe4], r12d                  
00abef80 jne      0xabef91                                      
00abef82 mov      rcx, rax                                      
00abef85 call     0x580d30                                      
00abef8a mov      rax, qword ptr [rip + 0x52f84b7]              
00abef91 mov      rax, qword ptr [rax + 0xb8]                   
00abef98 mov      rax, qword ptr [rax + 0x70]                   
00abef9c test     rax, rax                                      
00abef9f je       0xabf595                                      
00abefa5 mov      rax, qword ptr [rax + 0x50]                   
00abefa9 test     rax, rax                                      
00abefac je       0xabf595                                      
00abefb2 mov      rcx, qword ptr [rax + 0x38]                   
00abefb6 test     rcx, rcx                                      
00abefb9 je       0xabf595                                      
00abefbf mov      rdx, qword ptr [rip + 0x5275212]              
00abefc6 xor      r9d, r9d                                      
00abefc9 mov      r8, rsi                                       
00abefcc call     0x87b940                                      System.Void UIActionPrompt::Draw(System.String,System.String)
00abefd1 test     dil, dil                                      
00abefd4 je       0xabf27c                                      
00abefda mov      rdx, qword ptr [r15 + 0x2e0]                  
00abefe1 test     rdx, rdx                                      
00abefe4 jne      0xabefeb                                      
00abefe6 mov      rbx, r12                                      
00abefe9 jmp      0xabf028                                      
00abefeb mov      r8, qword ptr [rip + 0x5285e4e]               
00abeff2 mov      r9, qword ptr [rdx]                           
00abeff5 movzx    eax, byte ptr [r8 + 0x130]                    
00abeffd cmp      byte ptr [r9 + 0x130], al                     
00abf004 jb       0xabf01d                                      
00abf006 movzx    ecx, al                                       
00abf009 mov      rax, qword ptr [r9 + 0xc8]                    
00abf010 cmp      qword ptr [rax + rcx*8 - 8], r8               
00abf015 jne      0xabf01d                                      
00abf017 movzx    eax, r13b                                     
00abf01b jmp      0xabf01f                                      
00abf01d xor      al, al                                        
00abf01f test     al, al                                        
00abf021 mov      rbx, r12                                      
00abf024 cmovne   rbx, rdx                                      
00abf028 mov      rax, qword ptr [rip + 0x52f8419]              
00abf02f cmp      dword ptr [rax + 0xe4], r12d                  
00abf036 jne      0xabf047                                      
00abf038 mov      rcx, rax                                      
00abf03b call     0x580d30                                      
00abf040 mov      rax, qword ptr [rip + 0x52f8401]              
00abf047 mov      rax, qword ptr [rax + 0xb8]                   
00abf04e mov      rcx, qword ptr [rax + 0x70]                   
00abf052 test     rcx, rcx                                      
00abf055 je       0xabf595                                      
00abf05b mov      rcx, qword ptr [rcx + 0x88]                   
00abf062 test     rcx, rcx                                      
00abf065 je       0xabf595                                      
00abf06b xor      r9d, r9d                                      
00abf06e xor      r8d, r8d                                      
00abf071 mov      rdx, rbx                                      
00abf074 call     0x864f30                                      System.Boolean UIMonsterPopup::Draw(MonsterController,StatArray)
00abf079 mov      rcx, qword ptr [rip + 0x52f83c8]              
00abf080 mov      rdx, qword ptr [rcx + 0xb8]                   
00abf087 mov      rcx, qword ptr [rdx + 0x70]                   
00abf08b test     rcx, rcx                                      
00abf08e je       0xabf595                                      
00abf094 mov      rcx, qword ptr [rcx + 0x50]                   
00abf098 test     al, al                                        
00abf09a mov      rdx, r12                                      
00abf09d cmovne   rdx, rbx                                      
00abf0a1 test     rcx, rcx                                      
00abf0a4 je       0xabf595                                      
00abf0aa xor      r8d, r8d                                      
00abf0ad call     0x897850                                      System.Void UIGame::SetTarget(BaseUnitController)
00abf0b2 jmp      0xabf27c                                      
00abf0b7 mov      rcx, qword ptr [rip + 0x529cf82]              
00abf0be mov      rbx, qword ptr [r15 + 0x2e8]                  
00abf0c5 cmp      dword ptr [rcx + 0xe4], r12d                  
00abf0cc jne      0xabf0d3                                      
00abf0ce call     0x580d30                                      
00abf0d3 xor      edx, edx                                      
00abf0d5 mov      rcx, rbx                                      
00abf0d8 call     0x443daf0                                     
00abf0dd test     al, al                                        
00abf0df je       0xabf27c                                      
00abf0e5 mov      rax, qword ptr [r15 + 0x2e8]                  
00abf0ec test     rax, rax                                      
00abf0ef je       0xabf27c                                      
00abf0f5 mov      r8, qword ptr [rax]                           
00abf0f8 mov      rdx, qword ptr [rip + 0x5285d41]              
00abf0ff movzx    eax, byte ptr [rdx + 0x130]                   
00abf106 cmp      byte ptr [r8 + 0x130], al                     
00abf10d jb       0xabf27c                                      
00abf113 movzx    ecx, al                                       
00abf116 mov      rax, qword ptr [r8 + 0xc8]                    
00abf11d cmp      qword ptr [rax + rcx*8 - 8], rdx              
00abf122 jne      0xabf27c                                      
00abf128 mov      rax, qword ptr [rip + 0x52f8319]              
00abf12f cmp      dword ptr [rax + 0xe4], r12d                  
00abf136 jne      0xabf147                                      
00abf138 mov      rcx, rax                                      
00abf13b call     0x580d30                                      
00abf140 mov      rax, qword ptr [rip + 0x52f8301]              
00abf147 mov      rax, qword ptr [rax + 0xb8]                   
00abf14e mov      rax, qword ptr [rax + 0x70]                   
00abf152 test     rax, rax                                      
00abf155 je       0xabf595                                      
00abf15b mov      rax, qword ptr [rax + 0x50]                   
00abf15f test     rax, rax                                      
00abf162 je       0xabf595                                      
00abf168 mov      rcx, qword ptr [rax + 0x38]                   
00abf16c test     rcx, rcx                                      
00abf16f je       0xabf595                                      
00abf175 mov      rdx, qword ptr [rip + 0x527505c]              
00abf17c xor      r9d, r9d                                      
00abf17f mov      r8, rsi                                       
00abf182 call     0x87b940                                      System.Void UIActionPrompt::Draw(System.String,System.String)
00abf187 test     dil, dil                                      
00abf18a je       0xabf27c                                      
00abf190 mov      rax, qword ptr [r15 + 0x2e8]                  
00abf197 test     rax, rax                                      
00abf19a je       0xabf595                                      
00abf1a0 cmp      byte ptr [rip + 0x56add9c], r12b              
00abf1a7 mov      rdi, qword ptr [rax + 0x30]                   
00abf1ab jne      0xabf1d8                                      
00abf1ad lea      rcx, [rip + 0x5284bdc]                        
00abf1b4 call     0x5809f0                                      
00abf1b9 lea      rcx, [rip + 0x5336e60]                        
00abf1c0 call     0x5809f0                                      
00abf1c5 lea      rcx, [rip + 0x5336bdc]                        
00abf1cc call     0x5809f0                                      
00abf1d1 mov      byte ptr [rip + 0x56add6b], r13b              
00abf1d8 xor      edx, edx                                      
00abf1da mov      rcx, r15                                      
00abf1dd call     0xc22180                                      
00abf1e2 xor      edx, edx                                      
00abf1e4 mov      rcx, r15                                      
00abf1e7 test     al, al                                        
00abf1e9 je       0xabf265                                      
00abf1eb call     0xc22330                                      
00abf1f0 test     al, al                                        
00abf1f2 je       0xabf252                                      
00abf1f4 mov      rcx, qword ptr [rip + 0x5284b95]              
00abf1fb cmp      dword ptr [rcx + 0xe4], r12d                  
00abf202 jne      0xabf209                                      
00abf204 call     0x580d30                                      
00abf209 xor      ecx, ecx                                      
00abf20b call     0xc32a60                                      
00abf210 mov      rbx, rax                                      
00abf213 test     rax, rax                                      
00abf216 je       0xabf595                                      
00abf21c xor      r8d, r8d                                      
00abf21f mov      rdx, rdi                                      
00abf222 mov      rcx, rax                                      
00abf225 call     0xc113a0                                      
00abf22a xor      r9d, r9d                                      
00abf22d mov      qword ptr [rsp + 0x28], r12                   
00abf232 mov      r8, rbx                                       
00abf235 mov      dword ptr [rsp + 0x20], r12d                  
00abf23a mov      rcx, r15                                      
00abf23d lea      edx, [r9 + 0x16]                              
00abf241 call     0xc1f4b0                                      
00abf246 xor      edx, edx                                      
00abf248 mov      rcx, rbx                                      
00abf24b call     0xc2caf0                                      
00abf250 jmp      0xabf27c                                      
00abf252 xor      edx, edx                                      
00abf254 mov      rcx, r15                                      
00abf257 call     0xc22520                                      
00abf25c mov      rdx, qword ptr [rip + 0x5336dbd]              
00abf263 jmp      0xabf271                                      
00abf265 call     0xc22520                                      
00abf26a mov      rdx, qword ptr [rip + 0x5336b37]              
00abf271 xor      r8d, r8d                                      
00abf274 mov      rcx, rax                                      
00abf277 call     0xc66630                                      
00abf27c mov      dword ptr [r15 + 0x384], 0xffffffff           
00abf287 cmp      dword ptr [r15 + 0x454], r12d                 
00abf28e jl       0xabf2a9                                      
00abf290 mov      eax, dword ptr [r15 + 0x454]                  
00abf297 mov      dword ptr [r15 + 0x384], eax                  
00abf29e mov      dword ptr [r15 + 0x454], 0xffffffff           
00abf2a9 movups   xmm0, xmmword ptr [r15 + 0x328]               
00abf2b1 xor      r8d, r8d                                      
00abf2b4 lea      rdx, [rbp - 0x60]                             
00abf2b8 movups   xmm1, xmmword ptr [r15 + 0x338]               
00abf2c0 mov      rcx, r15                                      
00abf2c3 movaps   xmmword ptr [rbp - 0x60], xmm0                
00abf2c7 movups   xmm0, xmmword ptr [r15 + 0x348]               
00abf2cf movaps   xmmword ptr [rbp - 0x50], xmm1                
00abf2d3 movups   xmm1, xmmword ptr [r15 + 0x358]               
00abf2db movaps   xmmword ptr [rbp - 0x40], xmm0                
00abf2df movups   xmm0, xmmword ptr [r15 + 0x368]               
00abf2e7 movaps   xmmword ptr [rbp - 0x30], xmm1                
00abf2eb movups   xmm1, xmmword ptr [r15 + 0x378]               
00abf2f3 movaps   xmmword ptr [rbp - 0x20], xmm0                
00abf2f7 movups   xmm0, xmmword ptr [r15 + 0x388]               
00abf2ff movaps   xmmword ptr [rbp - 0x10], xmm1                
00abf303 movaps   xmmword ptr [rbp], xmm0                       
00abf307 call     0xad2f90                                      System.Void PlayerController::ProcessMovement(PlayerInputDto)
00abf30c xor      edx, edx                                      
00abf30e mov      rcx, r15                                      
00abf311 call     0xad32b0                                      System.Void PlayerController::ProcessSkills()
00abf316 movsd    xmm0, qword ptr [r15 + 0x328]                 
00abf31f mov      edx, dword ptr [r15 + 0x3a0]                  
00abf326 movsd    qword ptr [rsp + 0x30], xmm0                  
00abf32c movsd    xmm0, qword ptr [r15 + 0x398]                 
00abf335 movsd    qword ptr [rsp + 0x40], xmm0                  
00abf33b mov      eax, dword ptr [rsp + 0x30]                   
00abf33f cmp      dword ptr [rsp + 0x40], eax                   
00abf343 jne      0xabf452                                      
00abf349 mov      rcx, qword ptr [rsp + 0x30]                   
00abf34e mov      rax, qword ptr [rsp + 0x40]                   
00abf353 shr      rcx, 0x20                                     
00abf357 shr      rax, 0x20                                     
00abf35b cmp      eax, ecx                                      
00abf35d jne      0xabf452                                      
00abf363 cmp      edx, dword ptr [r15 + 0x330]                  
00abf36a mov      eax, r12d                                     
00abf36d sete     al                                            
00abf370 test     eax, eax                                      
00abf372 je       0xabf452                                      
00abf378 movzx    eax, byte ptr [r15 + 0x364]                   
00abf380 cmp      byte ptr [r15 + 0x3d4], al                    
00abf387 jne      0xabf452                                      
00abf38d movsd    xmm0, qword ptr [r15 + 0x334]                 
00abf396 mov      edx, dword ptr [r15 + 0x3ac]                  
00abf39d movsd    qword ptr [rsp + 0x30], xmm0                  
00abf3a3 movsd    xmm0, qword ptr [r15 + 0x3a4]                 
00abf3ac movsd    qword ptr [rsp + 0x40], xmm0                  
00abf3b2 mov      eax, dword ptr [rsp + 0x30]                   
00abf3b6 cmp      dword ptr [rsp + 0x40], eax                   
00abf3ba jne      0xabf452                                      
00abf3c0 mov      rcx, qword ptr [rsp + 0x30]                   
00abf3c5 mov      rax, qword ptr [rsp + 0x40]                   
00abf3ca shr      rcx, 0x20                                     
00abf3ce shr      rax, 0x20                                     
00abf3d2 cmp      eax, ecx                                      
00abf3d4 jne      0xabf452                                      
00abf3d6 cmp      edx, dword ptr [r15 + 0x33c]                  
00abf3dd mov      eax, r12d                                     
00abf3e0 sete     al                                            
00abf3e3 test     eax, eax                                      
00abf3e5 je       0xabf452                                      
00abf3e7 mov      eax, dword ptr [r15 + 0x36c]                  
00abf3ee cmp      dword ptr [r15 + 0x3dc], eax                  
00abf3f5 jne      0xabf452                                      
00abf3f7 mov      eax, dword ptr [r15 + 0x370]                  
00abf3fe cmp      dword ptr [r15 + 0x3e0], eax                  
00abf405 jne      0xabf452                                      
00abf407 mov      rdx, qword ptr [r15 + 0x378]                  
00abf40e xor      r8d, r8d                                      
00abf411 mov      rcx, qword ptr [r15 + 0x3e8]                  
00abf418 call     0x2dfff30                                     
00abf41d test     al, al                                        
00abf41f jne      0xabf452                                      
00abf421 mov      eax, dword ptr [r15 + 0x368]                  
00abf428 cmp      dword ptr [r15 + 0x3d8], eax                  
00abf42f jne      0xabf452                                      
00abf431 movzx    eax, byte ptr [r15 + 0x383]                   
00abf439 cmp      byte ptr [r15 + 0x3f3], al                    
00abf440 jne      0xabf452                                      
00abf442 mov      r14d, dword ptr [r15 + 0x384]                 
00abf449 not      r14d                                          
00abf44c shr      r14d, 0x1f                                    
00abf450 jmp      0xabf455                                      
00abf452 mov      r14d, r13d                                    
00abf455 mov      r8, qword ptr [rip + 0x52dde64]               
00abf45c mov      edx, r12d                                     
00abf45f mov      rax, qword ptr [r8 + 0xb8]                    
00abf466 mov      rcx, qword ptr [rax + 0x18]                   
00abf46a test     rcx, rcx                                      
00abf46d je       0xabf595                                      
00abf473 cmp      edx, dword ptr [rcx + 0x18]                   
00abf476 jge      0xabf514                                      
00abf47c lea      eax, [r12 - 0x28]                             
00abf481 cmp      eax, 3                                        
00abf484 jbe      0xabf4f5                                      
00abf486 xor      r8d, r8d                                      
00abf489 lea      rcx, [r15 + 0x328]                            
00abf490 mov      edx, r12d                                     
00abf493 call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abf498 xor      r8d, r8d                                      
00abf49b lea      rcx, [r15 + 0x328]                            
00abf4a2 mov      edx, r12d                                     
00abf4a5 movzx    ebx, al                                       
00abf4a8 call     0x715dd0                                      System.Boolean PlayerInputDto::GetHotkeyHeld(Hotkey)
00abf4ad xor      r8d, r8d                                      
00abf4b0 lea      rcx, [r15 + 0x398]                            
00abf4b7 mov      edx, r12d                                     
00abf4ba movzx    esi, al                                       
00abf4bd call     0x715df0                                      System.Boolean PlayerInputDto::GetHotkey(Hotkey)
00abf4c2 movzx    edi, al                                       
00abf4c5 lea      rcx, [r15 + 0x398]                            
00abf4cc xor      dil, bl                                       
00abf4cf xor      r8d, r8d                                      
00abf4d2 mov      edx, r12d                                     
00abf4d5 or       dil, r14b                                     
00abf4d8 call     0x715dd0                                      System.Boolean PlayerInputDto::GetHotkeyHeld(Hotkey)
00abf4dd mov      r8, qword ptr [rip + 0x52ddddc]               
00abf4e4 xor      al, sil                                       
00abf4e7 movzx    r14d, al                                      
00abf4eb test     dil, dil                                      
00abf4ee mov      eax, r13d                                     
00abf4f1 cmovne   r14d, eax                                     
00abf4f5 mov      rax, qword ptr [r8 + 0xb8]                    
00abf4fc inc      r12d                                          
00abf4ff mov      edx, r12d                                     
00abf502 mov      rcx, qword ptr [rax + 0x18]                   
00abf506 test     rcx, rcx                                      
00abf509 jne      0xabf473                                      
00abf50f jmp      0xabf595                                      
00abf514 movzx    eax, r14b                                     
00abf518 movaps   xmm9, xmmword ptr [rsp + 0x120]               
00abf521 movaps   xmm8, xmmword ptr [rsp + 0x130]               
00abf52a movaps   xmm7, xmmword ptr [rsp + 0x140]               
00abf532 movaps   xmm6, xmmword ptr [rsp + 0x150]               
00abf53a mov      r14, qword ptr [rsp + 0x160]                  
00abf542 mov      r13, qword ptr [rsp + 0x168]                  
00abf54a mov      rdi, qword ptr [rsp + 0x170]                  
00abf552 mov      rsi, qword ptr [rsp + 0x178]                  
00abf55a mov      rbx, qword ptr [rsp + 0x1a0]                  
00abf562 movaps   xmm10, xmmword ptr [rsp + 0x110]              
00abf56b add      rsp, 0x180                                    
00abf572 pop      r15                                           
00abf574 pop      r12                                           
00abf576 pop      rbp                                           
00abf577 ret                                                    
00abf578 xor      edx, edx                                      
00abf57a mov      rcx, r15                                      
00abf57d call     0xaef9f0                                      System.Void PlayerController::StopMovement()
00abf582 xor      al, al                                        
00abf584 jmp      0xabf518                                      
00abf586 xor      al, al                                        
00abf588 add      rsp, 0x180                                    
00abf58f pop      r15                                           
00abf591 pop      r12                                           
00abf593 pop      rbp                                           
00abf594 ret                                                    
00abf595 call     0x580ca0                                      
00abf59a int3                                                   
00abf59b int3                                                   
00abf59c int3                                                   
00abf59d int3                                                   
00abf59e int3                                                   
00abf59f int3                                                   

System.Boolean PlayerController::ProcessClickedUnit(BaseUnitController) RVA=0xad2a30
00ad2a30 mov      qword ptr [rsp + 0x18], rbx                   
00ad2a35 mov      qword ptr [rsp + 0x20], rsi                   
00ad2a3a mov      qword ptr [rsp + 0x10], rdx                   
00ad2a3f mov      qword ptr [rsp + 8], rcx                      
00ad2a44 push     rdi                                           
00ad2a45 sub      rsp, 0x60                                     
00ad2a49 mov      rsi, rdx                                      
00ad2a4c mov      rdi, rcx                                      
00ad2a4f cmp      byte ptr [rip + 0x569a465], 0                 
00ad2a56 jne      0xad2aa7                                      
00ad2a58 lea      rcx, [rip + 0x52e49e9]                        
00ad2a5f call     0x5809f0                                      
00ad2a64 lea      rcx, [rip + 0x52b090d]                        
00ad2a6b call     0x5809f0                                      
00ad2a70 lea      rcx, [rip + 0x52b0a39]                        
00ad2a77 call     0x5809f0                                      
00ad2a7c lea      rcx, [rip + 0x52b0b65]                        
00ad2a83 call     0x5809f0                                      
00ad2a88 lea      rcx, [rip + 0x527e501]                        
00ad2a8f call     0x5809f0                                      
00ad2a94 lea      rcx, [rip + 0x52895a5]                        
00ad2a9b call     0x5809f0                                      
00ad2aa0 mov      byte ptr [rip + 0x569a414], 1                 
00ad2aa7 mov      rax, qword ptr [rdi + 0x148]                  
00ad2aae test     rax, rax                                      
00ad2ab1 je       0xad2d8a                                      
00ad2ab7 mov      rdx, qword ptr [rax + 0x170]                  
00ad2abe test     rdx, rdx                                      
00ad2ac1 je       0xad2d8a                                      
00ad2ac7 mov      r8, qword ptr [rip + 0x527e4c2]               
00ad2ace lea      rcx, [rsp + 0x28]                             
00ad2ad3 call     0x18d51f0                                     
00ad2ad8 movups   xmm0, xmmword ptr [rsp + 0x28]                
00ad2add movups   xmmword ptr [rsp + 0x40], xmm0                
00ad2ae2 movsd    xmm1, qword ptr [rsp + 0x38]                  
00ad2ae8 movsd    qword ptr [rsp + 0x50], xmm1                  
00ad2aee mov      qword ptr [rsp + 0x28], 0                     
00ad2af7 lea      rbx, [rsp + 0x40]                             
00ad2afc mov      qword ptr [rsp + 0x30], rbx                   
00ad2b01 mov      rdx, qword ptr [rip + 0x52b09a8]              
00ad2b08 lea      rcx, [rsp + 0x40]                             
00ad2b0d call     0x299b470                                     
00ad2b12 test     al, al                                        
00ad2b14 je       0xad2b31                                      
00ad2b16 mov      rcx, qword ptr [rsp + 0x50]                   
00ad2b1b test     rcx, rcx                                      
00ad2b1e je       0xad2d90                                      
00ad2b24 xor      r8d, r8d                                      
00ad2b27 mov      rdx, rsi                                      
00ad2b2a call     0xad2a30                                      System.Boolean PlayerController::ProcessClickedUnit(BaseUnitController)
00ad2b2f jmp      0xad2b01                                      
00ad2b31 mov      rdx, qword ptr [rip + 0x52b0840]              
00ad2b38 mov      rcx, rbx                                      
00ad2b3b call     0x648670                                      System.Void Character::FootL()
00ad2b40 jmp      0xad2b6b                                      
00ad2b42 mov      rdx, qword ptr [rip + 0x52b082f]              
00ad2b49 mov      rcx, qword ptr [rsp + 0x30]                   
00ad2b4e call     0x648670                                      System.Void Character::FootL()
00ad2b53 mov      rcx, qword ptr [rsp + 0x28]                   
00ad2b58 test     rcx, rcx                                      
00ad2b5b jne      0xad2d96                                      
00ad2b61 mov      rsi, qword ptr [rsp + 0x78]                   
00ad2b66 mov      rdi, qword ptr [rsp + 0x70]                   
00ad2b6b mov      rcx, qword ptr [rip + 0x52894ce]              
00ad2b72 cmp      dword ptr [rcx + 0xe4], 0                     
00ad2b79 jne      0xad2b80                                      
00ad2b7b call     0x580d30                                      
00ad2b80 xor      edx, edx                                      
00ad2b82 mov      rcx, rsi                                      
00ad2b85 call     0x443daf0                                     
00ad2b8a test     al, al                                        
00ad2b8c je       0xad2d76                                      
00ad2b92 mov      rcx, qword ptr [rdi + 0x130]                  
00ad2b99 test     rcx, rcx                                      
00ad2b9c je       0xad2d8a                                      
00ad2ba2 xor      r8d, r8d                                      
00ad2ba5 mov      rdx, rsi                                      
00ad2ba8 call     0x84bcf0                                      System.Boolean CombatComponent::IsEnemy(BaseUnitController)
00ad2bad movzx    ebx, al                                       
00ad2bb0 xor      edx, edx                                      
00ad2bb2 mov      rcx, rdi                                      
00ad2bb5 call     0xc22620                                      
00ad2bba test     rax, rax                                      
00ad2bbd je       0xad2d8a                                      
00ad2bc3 xor      edx, edx                                      
00ad2bc5 mov      rcx, rax                                      
00ad2bc8 call     0xca75c0                                      
00ad2bcd test     bl, al                                        
00ad2bcf je       0xad2c1c                                      
00ad2bd1 mov      rax, qword ptr [rip + 0x52e4870]              
00ad2bd8 cmp      dword ptr [rax + 0xe4], 0                     
00ad2bdf jne      0xad2bf0                                      
00ad2be1 mov      rcx, rax                                      
00ad2be4 call     0x580d30                                      
00ad2be9 mov      rax, qword ptr [rip + 0x52e4858]              
00ad2bf0 mov      rax, qword ptr [rax + 0xb8]                   
00ad2bf7 mov      rcx, qword ptr [rax + 0x70]                   
00ad2bfb test     rcx, rcx                                      
00ad2bfe je       0xad2d8a                                      
00ad2c04 mov      rcx, qword ptr [rcx + 0x50]                   
00ad2c08 test     rcx, rcx                                      
00ad2c0b je       0xad2d8a                                      
00ad2c11 xor      r8d, r8d                                      
00ad2c14 mov      rdx, rsi                                      
00ad2c17 call     0x897850                                      System.Void UIGame::SetTarget(BaseUnitController)
00ad2c1c cmp      qword ptr [rdi + 0x438], 0                    
00ad2c24 jne      0xad2cca                                      
00ad2c2a test     bl, bl                                        
00ad2c2c je       0xad2d76                                      
00ad2c32 mov      qword ptr [rdi + 0x410], 0                    
00ad2c3d lea      rcx, [rdi + 0x410]                            
00ad2c44 xor      edx, edx                                      
00ad2c46 call     0x57fd40                                      
00ad2c4b mov      qword ptr [rdi + 0x440], 0                    
00ad2c56 lea      rcx, [rdi + 0x440]                            
00ad2c5d xor      edx, edx                                      
00ad2c5f call     0x57fd40                                      
00ad2c64 mov      rcx, qword ptr [rdi + 0x130]                  
00ad2c6b test     rcx, rcx                                      
00ad2c6e je       0xad2d8a                                      
00ad2c74 xor      r9d, r9d                                      
00ad2c77 xor      r8d, r8d                                      
00ad2c7a xor      edx, edx                                      
00ad2c7c call     0x84c9f0                                      System.Void CombatComponent::SetTarget(BaseUnitController,System.Boolean)
00ad2c81 mov      rcx, qword ptr [rdi + 0x120]                  
00ad2c88 test     rcx, rcx                                      
00ad2c8b je       0xad2d8a                                      
00ad2c91 xor      edx, edx                                      
00ad2c93 call     0x70a390                                      System.Void MoveComponent::Stop()
00ad2c98 mov      rcx, qword ptr [rdi + 0x130]                  
00ad2c9f test     rcx, rcx                                      
00ad2ca2 je       0xad2d8a                                      
00ad2ca8 xor      r9d, r9d                                      
00ad2cab xor      r8d, r8d                                      
00ad2cae mov      rdx, rsi                                      
00ad2cb1 call     0x84c9f0                                      System.Void CombatComponent::SetTarget(BaseUnitController,System.Boolean)
00ad2cb6 mov      al, 1                                         
00ad2cb8 lea      r11, [rsp + 0x60]                             
00ad2cbd mov      rbx, qword ptr [r11 + 0x20]                   
00ad2cc1 mov      rsi, qword ptr [r11 + 0x28]                   
00ad2cc5 mov      rsp, r11                                      
00ad2cc8 pop      rdi                                           
00ad2cc9 ret                                                    
00ad2cca mov      rcx, qword ptr [rdi + 0x120]                  
00ad2cd1 test     rcx, rcx                                      
00ad2cd4 je       0xad2d8a                                      
00ad2cda xor      edx, edx                                      
00ad2cdc call     0x70a390                                      System.Void MoveComponent::Stop()
00ad2ce1 mov      rcx, qword ptr [rdi + 0x138]                  
00ad2ce8 mov      rax, qword ptr [rdi + 0x438]                  
00ad2cef test     rax, rax                                      
00ad2cf2 je       0xad2d8a                                      
00ad2cf8 test     rcx, rcx                                      
00ad2cfb je       0xad2d8a                                      
00ad2d01 xor      r8d, r8d                                      
00ad2d04 mov      rdx, qword ptr [rax + 0x10]                   
00ad2d08 call     0x7bc220                                      SkillState SkillsComponent::GetAnySkill(System.String)
00ad2d0d test     rax, rax                                      
00ad2d10 je       0xad2d67                                      
00ad2d12 xor      edx, edx                                      
00ad2d14 mov      rcx, rax                                      
00ad2d17 call     0x7d6930                                      System.Boolean SkillState::get_IsOnCooldown()
00ad2d1c xor      al, 1                                         
00ad2d1e je       0xad2d67                                      
00ad2d20 mov      rcx, qword ptr [rdi + 0x138]                  
00ad2d27 test     rcx, rcx                                      
00ad2d2a je       0xad2d8a                                      
00ad2d2c xor      r9d, r9d                                      
00ad2d2f mov      r8, rsi                                       
00ad2d32 mov      rdx, qword ptr [rdi + 0x438]                  
00ad2d39 call     0x7b89e0                                      System.Boolean SkillsComponent::CanHit(SkillState,BaseUnitController)
00ad2d3e test     al, al                                        
00ad2d40 je       0xad2d67                                      
00ad2d42 mov      qword ptr [rdi + 0x440], rsi                  
00ad2d49 lea      rcx, [rdi + 0x440]                            
00ad2d50 mov      rdx, rsi                                      
00ad2d53 call     0x57fd40                                      
00ad2d58 xor      edx, edx                                      
00ad2d5a mov      rcx, rdi                                      
00ad2d5d call     0xabf740                                      System.Void PlayerController::CastOnTarget()
00ad2d62 jmp      0xad2cb6                                      
00ad2d67 xor      edx, edx                                      
00ad2d69 mov      rcx, rdi                                      
00ad2d6c call     0xac1050                                      System.Void PlayerController::ClearSkillReady()
00ad2d71 jmp      0xad2cb6                                      
00ad2d76 xor      al, al                                        
00ad2d78 lea      r11, [rsp + 0x60]                             
00ad2d7d mov      rbx, qword ptr [r11 + 0x20]                   
00ad2d81 mov      rsi, qword ptr [r11 + 0x28]                   
00ad2d85 mov      rsp, r11                                      
00ad2d88 pop      rdi                                           
00ad2d89 ret                                                    
00ad2d8a call     0x580ca0                                      
00ad2d8f nop                                                    
00ad2d90 call     0x580ca0                                      
00ad2d95 nop                                                    
00ad2d96 call     0x57cc20                                      
00ad2d9b int3                                                   
00ad2d9c int3                                                   
00ad2d9d int3                                                   
00ad2d9e int3                                                   
00ad2d9f int3                                                   
