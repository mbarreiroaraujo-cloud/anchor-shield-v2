use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod vulnerable_program {
    use super::*;

    pub fn process_data(ctx: Context<ProcessData>) -> Result<()> {
        // Reading data from an unverified account
        let data = ctx.accounts.data_source.try_borrow_data()?;
        let value = u64::from_le_bytes(data[8..16].try_into().unwrap());
        msg!("Value: {}", value);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ProcessData<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,

    /// No CHECK comment, no owner validation, no typed Account<T>
    pub data_source: AccountInfo<'info>,

    #[account(mut)]
    pub destination: AccountInfo<'info>,
}
